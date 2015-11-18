from flask import request, Response, send_from_directory
import logging
import os


def retrieve_image(app, date, regn_no, index):
    filename, mimetype = find_file(app.config['IMAGE_DIRECTORY'], date, regn_no, index)
    if filename is None:
        return None
    return send_from_directory(os.path.dirname(filename), os.path.basename(filename))


def create_update_image(app, date, regn_no, index):
    if request.headers['Content-Type'] != "image/tiff" and \
            request.headers['Content-Type'] != 'image/jpeg' and \
            request.headers['Content-Type'] != 'application/pdf':
        logging.error('Content-Type is not a valid image format')
        return Response(status=415)

    extn = get_extension(request.headers['Content-Type'])
    filename = '{}{}_{}_{}.{}'.format(app.config['IMAGE_DIRECTORY'], date, regn_no, index, extn)
    print("WRITE TO " + filename)
    file = open(filename, 'wb')
    file.write(request.data)
    file.close()
    return Response(status=201)


def remove_image(app, date, regn_no, index):
    filename, mimetype = find_file(app.config['IMAGE_DIRECTORY'], date, regn_no, index)
    if filename is None:
        return None
    os.remove(filename)
    return True


def find_file(directory, date, regn_no, index):
    filename_base = '{}{}_{}_{}'.format(directory, date, regn_no, index)
    filenames = [
        {'file': filename_base + '.jpeg', 'type': 'image/jpeg'},
        {'file': filename_base + '.tiff', 'type': 'image/tiff'},
        {'file': filename_base + '.pdf', 'type': 'application/pdf'}
    ]
    filename = None
    mimetype = None
    for file in filenames:
        if os.path.isfile(file['file']):
            filename = file['file']
            mimetype = file['type']
    if filename is None:
        return None, None
    return filename, mimetype


def get_extension(mimetype):
    if mimetype == "image/tiff":
        return 'tiff'
    elif mimetype == 'image/jpeg':
        return 'jpeg'
    elif mimetype == 'application/pdf':
        return 'pdf'
    return None
