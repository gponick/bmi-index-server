#!/usr/bin/env python3
"""
Very simple git caching http server for BMI, including modlist.json which can get popultaed externally.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import requests
import os
import pickle
import time
import json

MYAUTH = None

class S(BaseHTTPRequestHandler):

    # cache time in seconds
    CACHE_TIME = 60 * 60
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))

        realpath = os.path.join(os.path.realpath('.'),'cache')

        if('modlist.json' in self.path):
            if(os.path.exists(os.path.join(realpath,"modlist.json"))):
                self.send_response(200)
                self.end_headers()
                with open(os.path.join(realpath,"modlist.json"),'r') as ml:
                    logging.info("CACHE HIT: " + os.path.join(realpath, "modlist.json"))
                    datajson = ml.read()
                    self.wfile.write(bytes(datajson,'UTF-8'))
                    return
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes('{ "BTMLColorLOSMod": { "Website": "https://github.com/janxious/BTMLColorLOSMod/"} }','UTF-8'))
                return
        #print("NOW IN: {}".format(os.path.realpath('.')))

        try:
            os.makedirs(os.path.join(realpath + os.path.dirname(self.path)))
        except Exception as e:
            #print(e)
            pass

        if(os.path.exists(realpath + self.path + ".data")):
            if(time.time() - os.path.getmtime(realpath + self.path + ".data") <= (self.CACHE_TIME)):
                print("CACHE HIT FOR: {} --> [{}]".format(self.path, time.time() - os.path.getmtime(realpath + self.path + ".data")))
                with open(realpath + self.path + '.code', 'r') as rc:
                    with open(realpath + self.path + ".data",'r') as r:
                        with open(realpath + self.path + '.headers', 'rb') as rb:
                            newheaders = pickle.loads(rb.read())
                            self.send_response(int(rc.read()))
                            for header in newheaders:
                                if(header not in ("Content-Encoding", "Transfer-Encoding")):
                                    print("CACHE {}: {}".format(header, newheaders[header]))
                                    self.send_header(header, newheaders[header])
                            self.end_headers()
                        self.wfile.write(bytes(r.read(),'UTF-8'))
                        return

        #self._set_response()
        urltoget = 'https://api.github.com{}'.format(self.path.replace('/api/v3',''))
        logging.info(urltoget)
        response = requests.get(urltoget, auth=MYAUTH)
        self.send_response(response.status_code)
        for header in response.headers:
            if(header not in ("Content-Encoding", "Transfer-Encoding")):
                print("{}: {}".format(header, response.headers[header]))
                self.send_header(header, response.headers[header])
        self.end_headers()
        self.wfile.write(bytes(response.text,'UTF-8'))
        
    
        with open(os.path.join(realpath + self.path + '.headers'), 'wb') as fh:
            fh.write(pickle.dumps(response.headers))
        
        with open(os.path.join(realpath + self.path + '.code'),'w') as fc:
            fc.write(str(response.status_code))

        with open(os.path.join(realpath + self.path + ".data"),'w') as f:
            f.write(response.text)
    #self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=8086):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    if(os.path.exists(os.path.join(os.path.realpath('.'),'.credentials'))):
        with open(os.path.join(os.path.realpath('.'),'.credentials')) as setts:
            settingsjson = setts.read()
            newauth = json.loads(settingsjson)
            MYAUTH=(newauth["user"],newauth["password"])
            logging.info("User: " + MYAUTH[0])
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()