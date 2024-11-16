from intasend import APIService

API_PUBLISHABLE_KEY = 'ISPubKey_test_f89875d2-8db8-434b-864d-3ebc564d7afd'
API_TOKEN = 'ISSecretKey_test_be2d57dd-b5f6-47de-9b8a-24120ff8965c'

service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

create_order = service.collect.mpesa_stk_push(
    phone_number='25470174294', 
    email='danaobeid1@gmail.com', 
    amount=10, 
    narrative='Purchase of item'
)

print(create_order)
