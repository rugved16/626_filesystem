import os, shutil, socket, json
from pathlib import Path
from client import MAINSERVERHOST
import tests
import io
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
BLOCK_SIZE = 32
from Crypto.Util.Padding import pad, unpad
import codecs

key = 'abcdefghijklmnop'.encode()
ciphers = AES.new(key, AES.MODE_ECB)
decipher = AES.new(key, AES.MODE_ECB)



listOfYes = ["yes", "y", "YES", "Y"]
listOfNo = ["no", "n", "NO", "N"]
is_file = ["F", "FILE", "f", "file", ]
is_directory = ["D", "DIRECTORY", "d", "directory"]
KEY = bytes("0123456789abcdef", "utf-8")
IV = bytes(16)
FERNET_KEY = b'N8AcL6QxLj8UlcZvCnC5Fe-o6kOiebaGeF5gb1Qzwqo='
CIPHER = AES.new(KEY, AES.MODE_CBC, IV)
DECRYPTCIPHER = AES.new(KEY, AES.MODE_CBC, CIPHER.iv)
fernet = Fernet(FERNET_KEY)

#######################################################################################
# Display Help Menu
#######################################################################################
def help(ftp):
    print("============================\n",
          "\nCurrent Path: " + ftp.pwd() + "\n\n",
          "\t'q' == Quit SEDFS\n",
          "\t'r' == Read SEDFS file\n",
          "\t'w' == Write to SEDFS\n",
          "\t'p' == Change permissions\n",
          "\t'c' == Create new SEDFS file/directory\n",
          "\t'n' == Navigate to new directory\n",
          "\t'b' == Move back 1 directory\n",
          "\t'l' == List directory contents contents\n",
          "\t'd' == Delete file/directory\n",
          "\t's' == Display Server Information\n",
          "\t'o' == Open Text Editor\n",
          "\t'k' == Change Owner\n",
          "\t'u' == Rename File\n",
          "\t'h' == Help\n")

#
########################################################################################
# Open Text Editor
# Gets notepad on Windows, Nano on Linux
#######################################################################################
def open_program():
    text_editor = input("\nPlease enter text editor:\n >> ")
    file = input("\nPlease enter file:\n >> ")

    editor_path = shutil.which(text_editor)
    is_a_file = Path(file).is_file()

    if not editor_path:
        print(" << ERROR; Text Editor, '%s', does not exist", text_editor)
        return

    if not is_a_file:
        print(" << ERROR; Path incorrect or is not file")
        return

    try:
        os.system(editor_path + " " + file)
        print()

    except Exception as e:
        print(e)

#######################################################################################
# Makes a blank file or directory in SEDFS
#######################################################################################
def create_blank_file_or_directory(childServ, ftp, username, MAINSERVERHOST, MAINSERVERPORT):
    # loop until user says 'FILE' or 'DIRECTORY'
    while True:
        print(" >> File (F) or Directory (D)\n >> ", end='')
        response = input()

        if response in is_file or response in is_directory:
            break

    # create BLANK FILE
    if response in is_file:
        print("Create file name\n >> ", end='')
        client_file = input()

        # encrypt file name
        client_file = doEncrypt(client_file)
        print(client_file)

        command = 'STOR ' + client_file

        # create file for all servers
        try:
            response = ftp.storbinary(command, io.BytesIO(b''))
            print(" << ", response)

            for ser in childServ:
                ser.storbinary(command, io.BytesIO(b''))

            # ?????????????????
            createPermission("insert", doDecrypt(client_file), username, MAINSERVERHOST, MAINSERVERPORT)

        except Exception as e:
            print("------FAILED: File/Directory could not be made----------\n")
            print(" << ERROR:", e)
            return

        print("-------File creation completed successfully--------\n")

    # create BLANK DIRECTORY
    else:

        print("Create directory name\n >> ", end='')
        client_directory = input()


        # encypt directory name
        client_directory = doEncrypt(client_directory)

        try:
            response = ftp.mkd(client_directory)
            #print(" << ", response)
            print("------Directory created in parent server-----------\n")
            print("------Creating Directory in child servers----------\n")
            for ser in childServ:
                ser.mkd(client_directory)

            print("-------Directory creation completed successfully--------\n")

        except Exception as e:
            print(" << ERROR:", e)

#######################################################################################
#
#######################################################################################
def createPermission(flag, filename, owner, MAINSERVERHOST, MAINSERVERPORT, user=None):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((MAINSERVERHOST, MAINSERVERPORT))
        ip = socket.gethostbyname(socket.gethostname())

        #
        if flag=="insert":
            data = {"type":"insertPermissions", "fileDetails": {"name": filename, "owner": owner, "users":{}}}

        #
        else:
            data = {"type":"insertPermissions", "fileDetails": {"name": filename, "owner": owner, "users":{"name":user['name'],"per":user['per']}}}

        #
        jsData = json.dumps(data)
        sock.sendall(bytes(jsData, encoding="utf-8"))
        received = sock.recv(1024)
        data = received

        #
        return str(data)

#######################################################################################
# get permissions for a file
#######################################################################################
def getPermission(filename, username, MAINSERVERHOST, MAINSERVERPORT):

    #
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((MAINSERVERHOST, MAINSERVERPORT))
        data = {"type":"getPermissions", "filename":filename}
        jsData = json.dumps(data)
        sock.sendall(bytes(jsData, encoding="utf-8"))
        received = sock.recv(1024)

    #
    if received.decode('utf-8') == "NONE":
        return "owner"
    data = received.decode('utf-8')
    dat = json.loads(data)

    #
    if username == dat['owner']:
        return "owner"
    elif username in dat['users']:
        return dat['users'][username]
    else:
        return False


#######################################################################################
# delete permissions
#######################################################################################
def delPermission(filename, MAINSERVERHOST, MAINSERVERPORT):

    #
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((MAINSERVERHOST, MAINSERVERPORT))
        data = {"type":"delPermissions", "filename":filename}
        jsData = json.dumps(data)
        sock.sendall(bytes(jsData, encoding="utf-8"))
        received = sock.recv(1024)

    #
    data = received.decode('utf-8')


#######################################################################################
# update permissions
#######################################################################################
def updatePermission(oldfilename, newfilename, MAINSERVERHOST, MAINSERVERPORT):

    #
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((MAINSERVERHOST, MAINSERVERPORT))
        data = {"type":"updatePermissions", "oldfilename":oldfilename, "newfilename": newfilename}
        jsData = json.dumps(data)
        sock.sendall(bytes(jsData, encoding="utf-8"))
        received = sock.recv(1024)

    #
    data = received.decode('utf-8')

#######################################################################################
# Delete 'file' or 'directory'
#######################################################################################
def delete(ftp, childServ, username, MAINSERVERHOST, MAINSERVERPORT):
  
    name = input("Enter name to delete\n >> ")
    li = ftp.nlst()
    token = doEncrypt(name)
    permission = getPermission(name, username, MAINSERVERHOST, MAINSERVERPORT)
    if permission != "owner" and permission != "RW" and permission != "W":
        print("You don't have sufficient rights to delete the file.")
        return
    #for nam in li:
    #    if name == doDecrypt(nam):
    #       token = nam
    #if token == "":
    #    print("No sunch File found.....")
    #    return
    if not token in li:
        print("No such File found.....Please enter correct file name")
        return   

    # Ask if user wants new path
    while True:
        print("Do you want to enter new path?\n >> ", end='')
        ans = input().lower()

        if ans in listOfYes or ans in listOfNo:
            break
    #
    if ans in listOfNo:
        try:
            ftp.delete(token)
            for ser in childServ:
                ser.delete(token)
            delPermission(name, MAINSERVERHOST, MAINSERVERPORT)
            print("----------deletion successfully completed-------\n")
            return

        except Exception as e:
            print(e)
            return

    #
    else:
        print("Enter existing path\n >> ", end='')
        new_path = input()

        #
        try:
            ftp.delete(new_path + name)

            #
            for ser in childServ:
                ser[0].delete(new_path + name)
            delPermission(name, MAINSERVERHOST, MAINSERVERPORT)
            print("----------deletion successfully completed-------\n")
            return

        #
        except Exception as e:
            print(e)
            return

#######################################################################################
# navigate to new folder
#######################################################################################
def navigate(ftp, childServ):

    new_path = input("Enter new path\n >> ")

    # encrypt path
    enc_new_path = doEncrypt(new_path)

    # change current path in parent and all other child servers
    try:
        ftp.cwd(enc_new_path)
        for ser in childServ:
            ser.cwd(enc_new_path)

        print("-------Directory changed succesfully--------\n")

    except Exception as e:
        print(e)

#######################################################################################
# rename file on all known servers
#######################################################################################
def rename(ftp, childServ, MAINSERVERHOST, MAINSERVERPORT):

    resp = ''
    old_name = input("Enter the file name to rename \n >> ")
    new_name = input("Enter the new file name\n >> ")

    # encrypt oldname
    enc_old_name = doEncrypt(old_name)
    

    # encrypt newname
    enc_new_name = doEncrypt(new_name)

    try:
        resp = ftp.rename(enc_old_name, enc_new_name)
    except Exception as E:
        print(resp)
        print("------FAILED to rename file in parent server-------\n")
        return

    # rename files in child servers
    for ser in childServ:

        try:
            resp = ser.rename(enc_old_name, enc_new_name)
        except Exception as E:
            print(resp)
            print("------FAILED to rename file in ONE or MORE child servers-------\n")
            return
    updatePermission(old_name, new_name, MAINSERVERHOST, MAINSERVERPORT)
    print("------File renaming is completed succesfully-------\n")

#######################################################################################
# list all current files and directories
#######################################################################################
def ftp_list(ftp):

    try:
        print("\n\n-------Begin of List------\n")
        li = ftp.nlst()
        for i in li:
            print(doDecrypt(i))
        print("\n-------End of List------\n\n")

    except Exception as E:
        print("Error: ", E)

#######################################################################################
# change file permissions
#######################################################################################
def change_permissions(username, MAINSERVERHOST, MAINSERVERPORT):


    # encrypt file name
    filename = input("Input filename\n >> ")
    enc_filename = doEncrypt(filename)
    getper = getPermission(filename, username, MAINSERVERHOST, MAINSERVERPORT)
    if getper != "owner":
        print("You don't have enough rights to change permissions for the selected file")
        return

    # get permissions
    user = {}
    name = input("enter the user you want to assign permissions\n >>")
    user['name'] = name
    per = input("enter the permission type. 'R' for read access, 'RW' or 'W' for write access \n>>")
    if per == 'R' or per =='RW' or per == 'W':
        per = per
    else:
        per = "R"
    user['per'] = per
    #
    try:
        createPermission("update", filename, "", MAINSERVERHOST, MAINSERVERPORT, user)


    except Exception as E:
        print(E)


#######################################################################################
# change file permissions
#######################################################################################
def change_permissions_old(ftp, childServ):


    # encrypt file name
    filename = input("Input filename\n >> ")
    enc_filename = doEncrypt(filename)

    # get permissions
    permissions = input("Input new permissions\n >> ").strip()

    #
    try:
        ftp.sendcmd("SITE CHMOD " + permissions + " " + enc_filename)
        for ser in childServ:
            ser.sendcmd("SITE CHMOD" + permissions + " " + enc_filename)
        print("-------------Permission changed succesfully------------")


    except Exception as E:
        print(E)

#######################################################################################
#
#######################################################################################
def change_owner(ftp, childServ):

    # encrypt file name
    filename = input("Input filename\n >> ")
    enc_filename = doEncrypt(filename)

    owner = input("Input new owner\n >> ").strip()
    try:
        ftp.sendcmd("SITE CHOWN" + owner + " " + enc_filename)
        for ser in childServ:
            ser.sendcmd("SITE CHOWN" + owner + " " + enc_filename)
        print("-------------Owner changed succesfully------------")
    except Exception as E:
        print(E)

#######################################################################################
# upload local files to SEDFS
#######################################################################################
def uploadlocalfiles(ftp, childServ, username, MAINSERVERHOST, MAINSERVERPORT):

    # encrypt file
    local_name = input("Enter Local file path to upload\n >> ")
    enc_local_name = doEncrypt(local_name)

    # try to encrypt file and send it
    try:

        # open file
        with open(local_name, 'rb') as fo:
            plaintext = fo.read()

        # ENCRYPT ALL the file text
        enc_text = doEncrypt(str(plaintext))

        # Make encryted text as ".enc"
        with open(enc_local_name, 'w') as fo:
            fo.write(enc_text)

        print("\n-------File uploading started------")

    # failed to open / encrypt file
    except Exception as E:
        print(E)
        return

    # try to send ".enc" file
    try:

        # open encrypt file
        file_to_send = open(enc_local_name, 'rb')

        ftp.storbinary('STOR ' + enc_local_name, file_to_send)  # send the file
        print("-------File has uploaded to primary server----")
        print("-------Writing Files in child servers---------")

        # send file to all child servers
        for ser in childServ:
            fileChildServ = open(enc_local_name, 'rb')
            ser.storbinary('STOR ' + enc_local_name, fileChildServ)
            fileChildServ.close()
        createPermission("insert", local_name, username, MAINSERVERHOST, MAINSERVERPORT)
        os.remove(enc_local_name)
        print("-------File has uploaded successfully------\n\n")

    except Exception as E:
        print(E)


#######################################################################################
# write to SEDFS
#######################################################################################
def write(ftp, childServ, username, MAINSERVERHOST, MAINSERVERPORT):
    local_name = input("Enter Local file path to write\n >> ")
    enc_local_name = doEncrypt(local_name)
    getper = getPermission(local_name, username, MAINSERVERHOST, MAINSERVERPORT)
    if getper != "owner" and getper != "RW" and getper!="W":
        print("You don't have enough rights to  write for the selected file")
        return
    # Create a socket (SOCK_STREAM means a TCP socket)
    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        #sock.connect((MAINSERVERHOST, MAINSERVERPORT))
        #sock.sendall(bytes("getlockedfiles"+ "\n", "utf-8"))
        # Receive users data from the server and shut down
        #received = str(sock.recv(1024), "utf-8")
    #lockedfilelist = received.split(";")
    #print("locked file list:", lockedfilelist)
    #if local_name in lockedfilelist:
        #print("\nThe requested file is currently using by others, please try again later!!!\n")
        #return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((MAINSERVERHOST, MAINSERVERPORT))
        sock.sendall(bytes("lockfile:"+local_name+"\n", "utf-8"))
    try:
        li = ftp.nlst()
        print("file name: ",local_name)
        if enc_local_name in li:
            print("\n\n-------Begin of current content------\n")
            ftp.retrlines("RETR " + enc_local_name, fileLinePrinting)
            print("\n-------EOF------\n\n")
            newcontent = input("---------Enter content to append in the file\n------")
            enc_newcontent = doEncrypt(newcontent)
            file = open(enc_local_name, 'a')
            file.write(enc_newcontent)
            file.close()
            file1 = open(enc_local_name, 'rb')
            ftp.storbinary('STOR ' + enc_local_name, file1)
            file1.close()
            for ser in childServ:
                fileChildServ = open(enc_local_name, 'rb')
                ser.storbinary('STOR ' + enc_local_name, fileChildServ)
                fileChildServ.close()
            print("-------File has updated successfully------\n\n")
        else:
            try:
                print("\n-------File uploading started------")
                file = open(enc_local_name, 'w')
                newcontent = input("---------Enter content to write in the file\n------")
                file.write(enc_newcontent)
                file.close()
            except Exception as E:
                print(E)
                return
            try:
                file1 = open(enc_newcontent, 'rb')
                ftp.storbinary('STOR ' + enc_local_name, file1)  # send the file
                file1.close()
                print("-------File has uploaded to primary server----")
                print("-------Writing Files in child servers---------")
                for ser in childServ:
                    fileChildServ = open(enc_local_name, 'rb')
                    ser.storbinary('STOR ' + enc_local_name, fileChildServ)
                    fileChildServ.close()
                createPermission("insert", local_name, username, MAINSERVERHOST, MAINSERVERPORT)
                print("-------File has uploaded successfully------\n\n")
            except Exception as E:
                print(E)
    except Exception as E:
        print(E)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((MAINSERVERHOST, MAINSERVERPORT))
        sock.sendall(bytes("unlockfile:"+local_name+"\n", "utf-8"))

#######################################################################################
# update to SEDFS
#######################################################################################
def update(ftp, username, MAINSERVERHOST, MAINSERVERPORT, childServ):

    # encrypt local_name
    sedfs_name = input("Enter SEDFS file path to download\n >> ")
    enc_sedfs_name = doEncrypt(sedfs_name)
    getper = getPermission(sedfs_name, username, MAINSERVERHOST, MAINSERVERPORT)
    if getper != "owner" and getper != "RW" and getper!="W":
        print("You don't have enough rights to  write for the selected file")
        return
    try:
        print("\n\n-------Begin of current content------\n")
        ftp.retrlines("RETR " + enc_sedfs_name, fileLinePrinting)
        print("\n-------EOF------\n\n")
        newcontent = input("---------Enter content to append in the file\n------")
        enc_newcontent = doEncrypt(newcontent)
        file = open(enc_sedfs_name, 'a')
        file.write(enc_newcontent)
        file.close()
        file1 = open(enc_sedfs_name, 'rb')
        ftp.storbinary('STOR ' + enc_sedfs_name, file1)
        file1.close()
        for ser in childServ:
            fileChildServ = open(enc_sedfs_name, 'rb')
            ser.storbinary('STOR ' + enc_sedfs_name, fileChildServ)
            fileChildServ.close()
                  
        print("-------File has updated successfully------\n\n")
        
    except Exception as E:
        print(E)

#######################################################################################
# read from sedfs
#######################################################################################
def read(ftp, username, MAINSERVERHOST, MAINSERVERPORT):

    # encrypt local_name
    sedfs_name = input("Enter SEDFS file path to download\n >> ")
    enc_sedfs_name = doEncrypt(sedfs_name)
    getper = getPermission(sedfs_name, username, MAINSERVERHOST, MAINSERVERPORT)
    if getper != "owner" and getper != "RW" and getper!="W" and getper!="R":
        print("You don't have enough rights to  write for the selected file")
        return

    try:
        print("\n\n-------Begin------\n")
        ftp.retrlines("RETR " + enc_sedfs_name, fileLinePrinting)
        print("\n-------EOF------\n\n")

    except Exception as E:
        print(E)
        return

def fileLinePrinting(line):
    contentLine = "#%s#"%doDecrypt(line)
    print(contentLine)

#######################################################################################
# go back one directory
#######################################################################################
def go_back(ftp, childServ):
    # go back in current server, and other servers
    try:
        ftp.cwd("../")
        for ser in childServ:
            ser.cwd("../")

    # print error
    except Exception as E:
        print(E)


#######################################################################################
# encryption
#######################################################################################
def doEncrypt(content):
    #con = CIPHER.encrypt(pad(bytes(content, "utf-8"), AES.block_size))
    #result = b64encode(con).decode("utf-8")

    data = bytes(content, 'utf-8')
    msg = ciphers.encrypt(pad(data, BLOCK_SIZE))

    return codecs.encode(msg, 'hex').decode("utf-8")


#######################################################################################
# decryption
#######################################################################################
def doDecrypt(content):
    #result = DECRYPTCIPHER.decrypt(b64decode(content.encode("utf-8"))).decode("utf-8")
    content = content.encode("utf-8")
    data = codecs.decode(content, 'hex')
    plain_text = decipher.decrypt(data)
    msg_dec = unpad(plain_text, BLOCK_SIZE)
    return msg_dec.decode(encoding="utf-8")

#######################################################################################
# needed for error handling
#######################################################################################
class Execption:
    pass