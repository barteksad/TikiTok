import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography import x509

def check_token(token):
    n_decoded = jwt.get_unverified_header(token)
    kid_claim = n_decoded["kid"]

    response = requests.get("https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com")
    x509_key = response.json()[kid_claim]
    key = x509.load_pem_x509_certificate(x509_key.encode('utf-8'),  backend=default_backend())
    public_key = key.public_key()

    decoded_token = jwt.decode(token, public_key, ["RS256"], options=None, audience="jnp-auth")
    print(f"Decoded token : {decoded_token}")

idtoken = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFmZjFlNDJlNDE0M2I4MTQxM2VjMTI1MzQwOTcwODUxZThiNDdiM2YiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vam5wLWF1dGgiLCJhdWQiOiJqbnAtYXV0aCIsImF1dGhfdGltZSI6MTY3MTI4NjI0OCwidXNlcl9pZCI6IjAzSFlWNEptOHlWSlBpMHFnZXBNTHNjdkpWeTEiLCJzdWIiOiIwM0hZVjRKbTh5VkpQaTBxZ2VwTUxzY3ZKVnkxIiwiaWF0IjoxNjcxMzc5MDc1LCJleHAiOjE2NzEzODI2NzUsImVtYWlsIjoiZHNhQGRzLndwLnBsIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbImRzYUBkcy53cC5wbCJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.NLTHTrBkEPuIvswPZp-xDJUM-UCfNiYs1k51jitLyMgebP0kiQL34wntbSL8J3Plp3V3AnGnJRR4oQJZlTYblGTNug4S24moISDHvExQRN140hxOLPdOdpLAwHMNzkP5s5YQGdIeeQ-V_sp_KXxCnvlhLpCfhXcZgW6-49-FZk4rEwWaY-DdwbVObSJQMQYGTMinK6jmSbgHDzGgU7Fp5BMhKZuWdZxoDbiQtMDJSlB5sYSrsHsAwM4aljQey1r35AquFanaTRRjtyrrmfmMrZ_yC2CDBI0ekG6FAyy1477SGIvgHFjDZYy-5_qrx4kTWBEdoXLJCh_qytKr25qASQ";

check_token(idtoken)