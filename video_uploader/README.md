# Video Uploader

The uploader needs Firebase Admin config .json file to verify ID tokens. Env variable `GOOGLE_APPLICATION_CREDENTIALS` 
should contain the path to this config file inside the docker container. By default you can provide file `firebase-admin.json`
and place it in the same directory as this readme. You don't have to set the environment variable when using this approach.