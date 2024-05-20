import webview
webview.create_window("Bailey's chatroom", 'https://www.baileyschatroom.com/'
                    ,height=800,width=1200,resizable=True,min_size=(700,800))
webview.start(private_mode=False)
webview.settings = {
    'ALLOW_DOWNLOADS': False,
    'ALLOW_FILE_URLS': False,
    'OPEN_EXTERNAL_LINKS_IN_BROWSER': True,
    'OPEN_DEVTOOLS_IN_DEBUG': False
}