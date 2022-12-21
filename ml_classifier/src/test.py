import bunny_cdn as cdn

resp = cdn.get_video_object("4b5f7b9c-0625-4bee-9aaf-4387aad3a738")
print(resp.json())