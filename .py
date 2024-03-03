randomImageName = 'egg.png'
path = f"{{{{ url_for('static/usersUploaded', filename='{randomImageName}.png') }}}}"
print(path)
