import os

domain = ""
port = ""

def reloadPath():
    global domain
    global port
    with open("../domain.conf","r") as f:
        data = f.readlines()
        for line in data:
            if line.strip().startswith("domain:"):
                domain = line.split(":")[1].strip()
            elif line.strip().startswith("port:"):
                port = line.split(":")[1].strip()
                
def getPath():
    return "http://" + domain + ":" + port
    
reloadPath()
