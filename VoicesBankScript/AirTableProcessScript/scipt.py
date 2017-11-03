import requests
import json
import threading

API_KEY = 'keyxGk5Jw1Ph6GVHe'
EMAIL = 'patricialuciano@gmail.com'
DEBUG_EMAIL = 'mabreu91j@gmail.com'
DEBUG = True
MINIMUM_MATCH = 50
UPDATE_CASTING = True


#============ EMAIL ============

def send_simple_message(email,message,subject):
    if DEBUG:
        print 'sending email TO',email
        print 'subject', subject
        print 'message', message
        print '\n'
    
    return requests.post(
                         "https://api.mailgun.net/v3/sandbox3a82527eb98c48c2b535a8bde031fab8.mailgun.org/messages",
                         auth=("api", "key-3e1aca2a211db4bf9effb0419b4334e0"),
                         data={"from": "kasta.co <excited@sandbox3a82527eb98c48c2b535a8bde031fab8.mailgun.org>",
                         "to": email,
                         "subject": subject,
                         "text": message})

#============ AIRTABLE ============

def get_voice_actors():
    httpreturn = requests.get('https://api.airtable.com/v0/appUt7I5Jg9NUCDYu/Voice%20Talent',
                              headers={'Authorization': 'Bearer ' + API_KEY})
    return httpreturn.json()['records']

def get_castings():
    httpreturn = requests.get('https://api.airtable.com/v0/appUt7I5Jg9NUCDYu/Casting?view=Grid%20view',
                              headers={'Authorization': 'Bearer ' + API_KEY})
    return httpreturn.json()['records']

def get_jobs():
    httpreturn = requests.get('https://api.airtable.com/v0/appUt7I5Jg9NUCDYu/Jobs?view=Grid%20view',
                              headers={'Authorization': 'Bearer ' + API_KEY})
    return httpreturn.json()['records']

def put_casting(casting_id,data):
    requests.patch('https://api.airtable.com/v0/appUt7I5Jg9NUCDYu/Casting/'+casting_id,
                   data= json.dumps(data),
                   headers={'Authorization': 'Bearer ' + API_KEY
                   ,'Content-type': 'application/json'
                   },)

def put_jobs(job_id,data):
    requests.patch('https://api.airtable.com/v0/appUt7I5Jg9NUCDYu/Jobs/'+job_id,
                   data= json.dumps(data),
                   headers={'Authorization': 'Bearer ' + API_KEY
                   ,'Content-type': 'application/json'
                   },)

#============ UTILITIES ============

def dictionary_key_or_default(dict,key,default):
    if key in dict:
        return dict[key]
    return default

def casting_needs_processing(casting):
    return dictionary_key_or_default(casting['fields'],'Status','') == 'new'

def job_needs_processing(job):
    return not dictionary_key_or_default(job['fields'],'Processed',False)

def actor_invitation_message(client,campaing_name,brief,character_name,agency_brief_decription,agency_brief,amount,date):
    inviteMessage = ('Hola!\n\n'
                     'Te hemos preseleccionado para un casting del Banco de Voces abajo mas info al respecto:\n\n'
                     'La Marca '+client+'\n '
                     'Campana '+campaing_name+'\n\n '
                     'Aca una breve explicacion del esquema.\n '
                     ''+brief+'\n\n '
                     'Por favor, envianos notas de voz con el personaje '+character_name+' del siguiente documento.\n '
                     ''+agency_brief_decription+' || Link '+agency_brief+'\n\n '
                     'Por favor haz 3 tomas separadas. Las notas de voz deben llegar no mas de 2 horas desde que reciba este mensaje.\n\n '
                     'El monto de trabajo es: '+ amount+' menos nuestra comision del 30%\n '
                     'Este trabajo debe ser entregado antes de '+date+' \n\n '
                     'Muchas gracias y mucha suerte!')
    return inviteMessage

def job_requester_message():
    return "Hemos recibido tu solicitud.\n" \
        "En breve te contactaremos para completar el perfil que andas buscando para tu produccion. \n\n" \
            "Importante: En caso de aprobacion, favor de enviar la orden de compra al correo info@insidecommunications.com para procesar tu proyecto.\n\n" \
                "Gracias por contactarnos."


#============ EMAIL ============

def send_email(casting,matches):
    message = 'Process for casting: ' + dictionary_key_or_default(casting['fields'], 'Cliente', '{No name}')
    semaphore_matches = {"Neutral":[]}
    
    for match in matches:
        print match
    
    for match in matches:
        if 'Tipo de Talento' not in match[0]["fields"]:
            semaphore_matches["Neutral"].append(match)
        else:
            if match[0]["fields"]["Tipo de Talento"] not in semaphore_matches:
                semaphore_matches[match[0]["fields"]["Tipo de Talento"]] = []
            semaphore_matches[match[0]["fields"]["Tipo de Talento"]].append(match)

for key in semaphore_matches:
    print key
    
    message += '\n\n'
    for semaphore in semaphore_matches:
        message += '\n' + semaphore + '\n'
        for match in semaphore_matches[semaphore]:
            message += '\n' + dictionary_key_or_default(match[0]['fields'], 'Nombre', '') +  dictionary_key_or_default(
                                                                                                                       match[0]['fields'],
                                                                                                                       'Apellido', '') +  '  Match:' + str(int(match[1] * 100)) + '%'
        message += '\n\n'

    message += '\n\n\nMENSAJES PARA LOS ACTORES:\n\n\n'

message += actor_invitation_message(client=dictionary_key_or_default(casting['fields'], 'Cliente', '{No name}'),
                                    campaing_name=dictionary_key_or_default(casting['fields'], 'Campana', '{No name}'),
                                    brief=dictionary_key_or_default(casting['fields'], 'Brief Nuestro', '{No brief}'),
                                    character_name=dictionary_key_or_default(casting['fields'], 'Personaje', '{No name}'),
                                    agency_brief_decription=dictionary_key_or_default(casting['fields'], 'Descripcion Brief Agencia', '{No name}'),
                                    agency_brief="Brief agencia",
                                    amount=str(dictionary_key_or_default(casting['fields'], 'Monto', '{No name}')),
                                    date=str(dictionary_key_or_default(casting['fields'], 'Fecha del Trabajo', '{No name}'))
                                    )
    
    send_simple_message(EMAIL,message,'Casting recomendaciones')
    if DEBUG:
        send_simple_message(DEBUG_EMAIL, message, 'Casting recomendaciones')

#============ PROCESS  ============

def process_casting_with_actors(casting,voice_actors):
    matches = actors_match(voice_actors,casting)
    
    if UPDATE_CASTING:
        put_casting(casting['id'], {'fields': {'Status': 'processed'}})
    send_email(casting,matches)


def actor_match_percentage(actor, casting):
    
    actor_genero = dictionary_key_or_default(actor['fields'],"Genero",[])
    actor_languages = dictionary_key_or_default(actor['fields'],"Idiomas",[])
    casting_genero = dictionary_key_or_default(casting['fields'],"Genero",[])
    casting_languages = dictionary_key_or_default(casting['fields'],"Idiomas",[])
    
    if len(casting_genero) > 0:
        if actor_genero not in casting_genero:
            return 0
    if len(casting_languages) > 0:
        if not casting_languages <= actor_languages:
            return 0

casting_tags_set = set(dictionary_key_or_default(casting['fields'], 'Tags', []))
    actor_tags_set = set(dictionary_key_or_default(actor['fields'], 'Tags', []))
    match_percentage = float(len(actor_tags_set & casting_tags_set)) / float(len(casting_tags_set))
    
    return match_percentage

def actors_match(actors,casting):
    actors_and_match = []
    for actor in actors:
        match_percentage = actor_match_percentage(actor,casting)
        if match_percentage >= float(MINIMUM_MATCH) / 100.0:
            actors_and_match.append((actor, match_percentage))
    actors_and_match.sort(key=lambda x: x[1],reverse=True)
    return actors_and_match

def process():
    voice_actors = None
    try:
        for casting in get_castings():
            if casting_needs_processing(casting):
                if not voice_actors:
                    voice_actors = get_voice_actors()
                process_casting_with_actors(casting, voice_actors)
    except:
        pass


    for job in get_jobs():
        if job_needs_processing(job):
            message = job_requester_message()
            client = dictionary_key_or_default(job["fields"],"Productor","{Nombre no especificado}")
            
            self_title = "Nuevo Job!!"
            self_message = "Nuevo job de " + client
            
            if "Email" in job["fields"]:
                requester_email = job["fields"]["Email"]
                send_simple_message(requester_email,message,"Solicitud recibida!")
            else:
                self_message = self_message + "\n" + "No pudimos enviarle una notificacion via email al solicitante."
            
            send_simple_message(EMAIL, self_message, self_title)
            if DEBUG:
                send_simple_message(DEBUG_EMAIL, self_message, self_title)
            put_jobs(job["id"], {'fields': {'Processed': True}})


#============ MAIN ============
while True:
    process()
    print "SLEEPING"
    threading._sleep(100)
