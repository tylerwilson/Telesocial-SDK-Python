Telesocial API SDK for Python
-----------------------------

Telesocial's calling API enables mobile calling via social networks. This is a Python
interface to Telesocials REST API. See http://dev.telesocial.com/ for more information.


Requirements
------------

- Python 2.7 or above, including Python 3.x


Supported Features
------------------



Testing framework
-----------------

Unittests


GUI application

There is a PyGTK/PyQT/PySide(?) application which emulates the Telesocial SDK
sample here: https://sb.telesocial.com/demo-web/


Example Usage (based on Ruby version)
-------------

import telesocial

client = telesocial.SimpleClient('your_api_key') # Now, all telesocial methods are available to your client

# Method calls on the client returns a simple object that includes a sub-structure that matches
# Telesocial's API response object, within the 

# Register a user with username "eric" and phone number: 14054441212
response = client.network_id_register(network_id="eric", phone="14054441212")
print(response.status) # => 201
print(response.uri) # => "/api/rest/registrant/eric"

# Check a user's registration status
response = client.network_id_status('eric')

# Upload a file to be played to a registered user
media_id = client.media_create()
upload_request_grant_id = client.media_request_upload_grant(media_id)

uploaded_file_url = client.upload_file(upload_request_grant_id, "my_file_path.mp3")