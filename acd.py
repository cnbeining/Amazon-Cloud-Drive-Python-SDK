#!/usr/bin/env python
#coding:utf-8
# Author: Beining --<cnbeining@gmail.com>
# Purpose: A basic SDK for Amazon Cloud Drive
# Created: 04/03/2015

import sys
import os
import urllib
import urllib2
import requests
import requests_toolbelt
import time
import json
import logging
import unittest

global LOGIN_DICT
global USER_AGENT
LOGIN_DICT = {
 'client_id': 'amzn1.application-oa2-client.',
 'client_secret': '',
 'redirect_uri': 'https://',
 'token_type': '',
 'expire_unix_time': 0,
 'refresh_token': '',
 'access_token': '',
 'contentUrl': '',
 'metadataUrl': '',
 }
USER_AGENT = 'Amazon Cloud Drive Python SDK/0.0.1 (cnbeining@gmail.com)'

########################################################################
class AmazonCloudDriveBase:
    """"""

    #----------------------------------------------------------------------
    def __init__(self, LOGIN_DICT):
        """Constructor"""
        self.login_dict = LOGIN_DICT
        
    #----------------------------------------------------------------------
    def login(self):
        """Login with Authorization Code Grant
        https://developer.amazon.com/public/apis/experience/cloud-drive/content/getting-started"""
        print('''
Logging you in with OAuth2...
        
Please visit:
https://www.amazon.com/ap/oa?client_id={client_id}&scope=clouddrive%3Aread%20clouddrive%3Awrite&response_type=code&redirect_uri={redirect_uri}
        
and authorize this app.
You should be shown the code.
        
If not, check the URL, which should looks like
https://www.poi.poi/poi?code=ANAuMZiBZUyJKFMnOcKB&scope=clouddrive%3Aread+clouddrive%3Awrite ,
        
then in this case, "ANAuMZiBZUyJKFMnOcKB" is the code.
        
Please kindly paste the code here, then press ENTER. ''').format(client_id = self.login_dict['client_id'], redirect_uri = self.login_dict['redirect_uri'])
        code_raw = str(raw_input()).strip()
        print('Retriving token...')
        payload = {'grant_type': 'authorization_code',
                   'code': code_raw,
                   'client_id': self.login_dict['client_id'],
                   'client_secret': self.login_dict['client_secret'],
                   'redirect_uri': self.login_dict['redirect_uri']}
        headers = {'Cache-Control': 'no-cache', 'User-Agent': USER_AGENT}
        r = requests.post('https://api.amazon.com/auth/o2/token', data=payload, headers=headers)
        if r.status_code != 200:
            print('ERROR: Cannot login!')
            raise ErrorLoginException(r.content)
        else:
            self.login_dict['token_type'] = r.json()['token_type']
            self.login_dict['access_token'] = r.json()['access_token']
            self.login_dict['expire_unix_time'] = int(time.time()) + int(r.json()['expires_in'])
            self.login_dict['refresh_token'] = r.json()['refresh_token']
        self.set_endpoint()
        print('Login successful!')
        LOGIN_DICT = self.login_dict
    
    #----------------------------------------------------------------------
    def refresh(self):
        """refresh access_token with refresh_token, since access_token expires every 3600 secs.
        https://developer.amazon.com/public/apis/experience/cloud-drive/content/getting-started"""
        logging.debug('Refreshing...')
        logging.debug(self.login_dict)
        payload = {'grant_type': 'refresh_token',
                   'refresh_token': self.login_dict['refresh_token'],
                   'client_id': self.login_dict['client_id'],
                   'client_secret': self.login_dict['client_secret']}
        headers = {'Cache-Control': 'no-cache', 'User-Agent': USER_AGENT}
        r = requests.post('https://api.amazon.com/auth/o2/token', data=payload, headers=headers)
        if r.status_code != 200:
            print('ERROR: Cannot refresh!')
            raise ErrorLoginException(r.content)
        else:
            self.login_dict['token_type'] = r.json()['token_type']
            self.login_dict['access_token'] = r.json()['access_token']
            self.login_dict['expire_unix_time'] = int(time.time()) + int(r.json()['expires_in'])
            self.login_dict['refresh_token'] = r.json()['refresh_token']
        logging.debug('Refresh successful!')
        # print('Refresh successful!')
        LOGIN_DICT = self.login_dict
    
    #----------------------------------------------------------------------
    def check_need_refresh(self):
        """"""
        if int(time.time()) >= int(self.login_dict['expire_unix_time']):
            logging.debug('Need refresh')
            self.refresh()
    
    #----------------------------------------------------------------------
    def set_endpoint(self):
        """"""
        logging.debug('Fetching endpoints')
        headers = {'Cache-Control': 'no-cache', 'User-Agent': USER_AGENT, 'Authorization': 'Bearer ' + self.login_dict['access_token']}
        r = requests.get('https://drive.amazonaws.com/drive/v1/account/endpoint', headers=headers)
        if r.status_code != 200:
            print('ERROR: Cannot get endpoint!')
            raise ErrorLoginException(r.content)
        else:
            self.login_dict['contentUrl'] = r.json()['contentUrl']
            self.login_dict['metadataUrl'] = r.json()['metadataUrl']
    
    #----------------------------------------------------------------------
    def send_request(self, url, refresh = True, method = 'get', put_data = '', post_data = '', patch_data = ''):
        """A wrapper to fix all the authorization
        Everything after login"""
        self.check_need_refresh()
        headers = {'Cache-Control': 'no-cache', 'User-Agent': USER_AGENT, 'Authorization': 'Bearer ' + self.login_dict['access_token']}
        if method == 'get':
            r = requests.get(url, headers=headers)
        elif method == 'put':
            r = requests.put(url, data=put_data, headers=headers)
        elif method == 'post':  #!!!!!!!!!!!!!!!!!!!
            r = requests.post(url, data=post_data, headers=headers)
        elif method == 'patch':  #!!!!!!!!!!!!!!!!!!!
            r = requests.patch(url, data=patch_data, headers=headers)
        elif method == 'delete':
            r = requests.delete(url, headers=headers)
        logging.debug('Status: ' + str(r.status_code))
        logging.debug(r.json())
        print(r.content)
        if r.status_code == 401 and refresh:
            logging.info('Refreshing Token...')
            self.refresh()
            return self.send_request(url, refresh = False, method = 'get', put_data = '')
        return r.json()
    
    #----------------------------------------------------------------------
    def dump_info(self, filename):
        """"""
        with open(filename, 'w') as f:
            json.dump(self.login_dict, f)
    
    #----------------------------------------------------------------------
    def load_info(self, filename):
        """"""
        global LOGIN_DICT
        with open(filename, 'r') as f:
            LOGIN_DICT = json.load(f)
        self.login_dict = LOGIN_DICT
    
    #----------------------------------------------------------------------
    def login_dict(self):
        """"""
        return self.login_dict

########################################################################
class AmazonCloudDriveAccount(AmazonCloudDriveBase):
    """https://developer.amazon.com/public/apis/experience/cloud-drive/content/account"""

    #----------------------------------------------------------------------
    def __init__(self, LOGIN_DICT):
        """Constructor"""
        AmazonCloudDriveBase.__init__(self, LOGIN_DICT)
        #AmazonCloudDriveBase().refresh()
        self.metadataUrl = AmazonCloudDriveBase.login_dict(self)['metadataUrl']
    
    #----------------------------------------------------------------------
    def info(self):
        """"""
        url = self.metadataUrl + '/account/info'
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get', put_data = '')
        self.info = {'status': result['status'], 'termsOfUse': result['termsOfUse']}
        return self.info
    
    #----------------------------------------------------------------------
    def endpoint(self):
        """Automaticly fixed with the Base, just put it here in case you want to use it"""
        url = self.metadataUrl + '/account/endpoint'
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get', put_data = '')
        #print(result)
        AmazonCloudDriveBase(LOGIN_DICT).set_endpoint()  #Yeah, I know you want to change it
        self.endpoint = {'contentUrl': result['contentUrl'], 'metadataUrl': result['metadataUrl'], 'customerExists': result['customerExists']}
        return self.endpoint
    
    #----------------------------------------------------------------------
    def quota(self):
        """The result is not exactly the same as the document:
        {u'available': 5368709120, u'benefits': [], u'plans': [u'CDSPUS0001'], u'quota': 5368709120, u'lastCalculated': u'2015-04-03T21:26:20.640Z', u'grants': []}"""
        url = self.metadataUrl + '/account/quota'
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get', put_data = '')
        #print(result)
        self.quota = {'available': result['available'], 'quota': result['quota'], 'lastCalculated': result['lastCalculated']}
        return self.quota
    
    #----------------------------------------------------------------------
    def usage(self):
        """RETURNS JSON!!!"""
        url = self.metadataUrl + '/account/usage'
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get', put_data = '')
        self.usage = result
        return self.usage

########################################################################
class AmazonCloudDriveNodes(AmazonCloudDriveBase, AmazonCloudDriveAccount):
    """https://developer.amazon.com/public/apis/experience/cloud-drive/content/account"""

    #----------------------------------------------------------------------
    def __init__(self, LOGIN_DICT):
        """Constructor"""
        AmazonCloudDriveBase.__init__(self, LOGIN_DICT)
        #AmazonCloudDriveBase().refresh()
        self.metadataUrl = AmazonCloudDriveBase.login_dict(self)['metadataUrl']
        self.contentUrl = AmazonCloudDriveBase.login_dict(self)['contentUrl']
        self.Authorization = "Authorization: Bearer " + AmazonCloudDriveBase.login_dict(self)['access_token']
    
    #----------------------------------------------------------------------
    def upload_file_curl(self, local_path, parents='', labels = '', properties = []):
        """"""
        name = os.path.basename(local_path)
        url = self.contentUrl + 'nodes?&suppress=deduplication'
        metadata = {"name": name, "kind": "FILE"}
        if parents:
            metadata['parents'] = parents
        if labels:
            metadata['labels'] = labels
        if properties:
            metadata['properties'] = properties
        command = 'curl -k -X POST --form "metadata={metadata}"  --form "content=@{local_path}" "{url}" --header  "{Authorization}"' .format(metadata = metadata, local_path = local_path, url = url, Authorization = self.Authorization)
        logging.debug(command)
        tmp = os.popen(command).readlines()
        #print(tmp)[0]
        return json.loads(tmp[0])
        
    #----------------------------------------------------------------------
    def overwrite_file_curl(self, local_path, id):
        """NOT TESTED
        """
        url = self.contentUrl + 'nodes/{id}/content'.format(id = id)
        command = 'curl -k -X POST  --form "content=@{local_path}" "{url}" --header  "{Authorization}"' .format(local_path = local_path, url = url, Authorization = self.Authorization)
        logging.debug(command)
        tmp = os.popen(command).readlines()
        #print(tmp)[0]
        return json.loads(tmp[0])
    
    #----------------------------------------------------------------------
    def get_file(self, id, assetMapping = 'NONE', tempLink = 'false'):
        """RETURNS JSON!"""
        url = self.metadataUrl + '/nodes/{id}?&tempLink={tempLink}'.format(id = id, assetMapping = assetMapping, tempLink = tempLink)  #asset={assetMapping}
        logging.debug(url)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get', put_data = '')
        return result
    
    #----------------------------------------------------------------------
    def patch_file(self, id, payload):
        """NOT TESTED
        RETURNS JSON!"""
        url = self.metadataUrl + '/nodes/{id}?asset={assetMapping}&tempLink={tempLink}'.format(id = id, assetMapping = assetMapping, tempLink = tempLink)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'patch', patch_data = payload)
        return result
    
    #----------------------------------------------------------------------
    def list_file(self, **kargs):
        """RETURNS JSON!
        Avalable arguments:
        filters: (Optional) filters for request, see filtering 
        startToken: (Optional) nextToken from previous request for access more content, see pagination 
        sort : (Optional) to order the result in sorted manner, see sorting 
        limit : (Optional) default to 200. Limit the number of file metadata to be returned. 
        assetMapping : (Optional) default NONE, see assetMapping 
        tempLink : (Optional) default false, set true to include tempLink in response"""
        url = self.metadataUrl + '/drive/v1/nodes?'
        for key, value in kwargs.iteritems():
            url += '&{key}={value}'.format(key = key, value = value)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get')
        return result
    
    #----------------------------------------------------------------------
    def download_file_curl(self, id, local_path = ''):
        """Yes, you can easily modify it to other softwares
        or, go with tempLink!"""
        url = self.contentUrl + 'nodes/{id}/content'.format(id = id)
        if not local_path:  #download to the current path with original name
            local_path = self.get_file(id)['name']
        command = 'curl -k "{url}" -o {local_path} --header  "{Authorization}"' .format(local_path = local_path, url = url, Authorization = self.Authorization)
        logging.debug(command)
        tmp = os.popen(command).readlines()
        
    #----------------------------------------------------------------------
    def create_folder(self, folder_name, localId = '', labels = [], properties = {}, parents = []):
        """RETURNS JSON!
        labels : (optional) Extra information which is indexed. For example the value can be "SpringBreak" 
        properties : (optional) List of properties to be added for the folder. 
        parents : (optional) List of parent Ids. If no parent folders are provided, the folder will be placed in the default root folder."""
        url = self.metadataUrl + 'nodes'
        if localId:
            url += '?localId={localId}'.format(localId = urllib.quote_plus(folder_name))
        payload = {"name": urllib.quote_plus(folder_name), "kind": 'FOLDER'}
        logging.debug(url)
        post_data = str(payload).replace("'", '"')
        logging.debug(post_data)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'post', post_data = post_data)
        return result
    
    #----------------------------------------------------------------------
    def get_folder(self, id):
        """"""
        url = self.metadataUrl + 'nodes/{id}'.format(id = id)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get')
        return result
    
    #----------------------------------------------------------------------
    def patch_folder(self, id, name = '', labels = [], description = ''):
        """NOT TESTED
        RETURNS JSON!"""
        url = self.metadataUrl + '/nodes/{id}'.format(id = id)
        payload = ''
        if name:
            payload['name'] = name
        if labels:
            payload['labels'] = labels
        if description:
            payload['description'] = description
        patch_data = str(payload).replace("'", '"')
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'patch', patch_data = payload)
        return result
    
    #----------------------------------------------------------------------
    def list_folder(self, **kargs):
        """NOT TESTED
        RETURNS JSON!
        Avalable arguments:
        filters: (Optional) filters for request, see filtering 
        startToken: (Optional) nextToken from previous request for access more content, see pagination """
        url = self.metadataUrl + '/drive/v1/nodes?'
        for key, value in kwargs.iteritems():
            url += '&{key}={value}'.format(key = key, value = value)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get')
        return result
    
    #----------------------------------------------------------------------
    def add_children(self, parentId, childId):
        """"""
        url = self.metadataUrl + 'nodes/{parentId}/children/{childId}'.format(parentId = parentId, childId = childId)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'put')
        return result
    
    #----------------------------------------------------------------------
    def delete_children(self, parentId, childId):
        """NOT TESTED"""
        url = self.metadataUrl + 'nodes/{parentId}/children/{childId}'.format(parentId = parentId, childId = childId)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'delete')
        return result
    
    #----------------------------------------------------------------------
    def list_children(self, id, **kargs):
        """NOT TESTED
        RETURNS JSON!
        Avalable arguments:
        filters: (Optional) filters for request, see filtering 
        startToken: (Optional) nextToken from previous request for access more content, see pagination """
        url = self.metadataUrl + 'nodes/{id}/children'.format(id = id)
        for key, value in kwargs.iteritems():
            url += '&{key}={value}'.format(key = key, value = value)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get')
        return result
    
    #----------------------------------------------------------------------
    def add_property(self, id, owner, key, property = ''):
        """NOT TESTED"""
        url = self.metadataUrl + 'nodes/{id}/properties/{owner}/{key}'.format(id = id, owner = owner, key = key)
        post_data = str(property).replace("'", '"')
        logging.debug(post_data)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'post', post_data = post_data)
        return result
    
    #----------------------------------------------------------------------
    def list_property(self, id, owner):
        """NOT TESTED"""
        url = self.metadataUrl + 'nodes/{id}/properties/{owner}'.format(id = id, owner = owner)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get')
        return result
    
    #----------------------------------------------------------------------
    def get_property(self, id, owner, key):
        """NOT TESTED"""
        url = self.metadataUrl + 'nodes/{id}/properties/{owner}/{key}'.format(id = id, owner = owner, key = key)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get')
        return result
    
    #----------------------------------------------------------------------
    def delete_property(self, id, **kargs):
        """NOT TESTED
        RETURNS JSON!
        Avalable arguments:
        filters: (Optional) filters for request, see filtering 
        startToken: (Optional) nextToken from previous request for access more content, see pagination """
        url = self.metadataUrl + 'nodes/{id}/properties/{owner}/{key}'.format(id = id, owner = owner, key = key)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'delete')
        return result
    ##----------------------------------------------------------------------
    #def upload_file(self, filename):
        #"""UNUSABLE"""
        #url = self.contentUrl + '/nodes'
        #post_form = {'content': open(filename, 'rb'), 'metadata': '{"name":"fooo.jpg","kind":"FILE"}'}
        #result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'post', put_data = '', post_data = post_form)
    
    ##----------------------------------------------------------------------
    #def upload_child_file(self, local_path, parents='', labels = '', properties = []):
        #'''UNUSABLE'''
        #name = os.path.basename("/Users/Beining/Movies/flight.py")
        #url = self.contentUrl + 'nodes?&suppress=deduplication'
        #print(url)
        ##logging.info("Uploading %s to %s", local_path)
        #metadata = {"name": name, "kind": "FILE"}
        #if parents:
            #metadata['parents'] = parents
        #if labels:
            #metadata['labels'] = labels
        #if properties:
            #metadata['properties'] = properties
        #m = requests_toolbelt.MultipartEncoder([
            #("metadata", json.dumps(metadata)),
            #("content", (name, open(local_path, "rb")))])
        #result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'post', put_data = '', post_data = m)
        
        ##self.info = {'status': result['status'], 'termsOfUse': result['termsOfUse']}
        ##print(result)
        #return result

########################################################################
class AmazonCloudDriveChanges(AmazonCloudDriveBase):
    """https://developer.amazon.com/public/apis/experience/cloud-drive/content/changes"""

    #----------------------------------------------------------------------
    def __init__(self, LOGIN_DICT):
        """Constructor"""
        AmazonCloudDriveBase.__init__(self, LOGIN_DICT)
        #AmazonCloudDriveBase().refresh()
        self.metadataUrl = AmazonCloudDriveBase.login_dict(self)['metadataUrl']
    
    #----------------------------------------------------------------------
    def info(self, checkpoint = '', chunkSize = 0, maxNodes = 0, includePurged = False):
        """
        checkpoint (optional) : A token representing a frontier of updated items. 
        chunkSize (optional) : The number of nodes to be returned within each Changes object in the response stream. 
        maxNodes (optional) : The threshold of number of nodes returned at which the streaming call will be ended. This is not intended to be used for strict pagination as the number of nodes returned may exceed this number. 
        includePurged (optional) : If true then it will return the purged nodes as well. Default to false."""
        url = self.metadataUrl + '/changes'
        payload = {}
        if checkpoint:
            payload['checkpoint'] = checkpoint
        if chunkSize:
            payload['chunkSize'] = chunkSize
        if maxNodes:
            payload['maxNodes'] = maxNodes
        if includePurged:
            payload['includePurged'] = includePurged
        post_data = str(payload).replace("'", '"')
        logging.debug(post_data)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'post', post_data = post_data)
        return result

########################################################################
class AmazonCloudDriveTrash(AmazonCloudDriveBase, AmazonCloudDriveNodes):
    """https://developer.amazon.com/public/apis/experience/cloud-drive/content/trash"""

    #----------------------------------------------------------------------
    def __init__(self, LOGIN_DICT):
        """Constructor"""
        AmazonCloudDriveBase.__init__(self, LOGIN_DICT)
        #AmazonCloudDriveBase().refresh()
        self.metadataUrl = AmazonCloudDriveBase.login_dict(self)['metadataUrl']
    
    #----------------------------------------------------------------------
    def add(self, id):
        """"""
        url = self.metadataUrl + '/trash/{id}'.format(id = id)
        file_info = AmazonCloudDriveNodes(LOGIN_DICT).get_file(id,  tempLink = 'false')
        #print(file_info)
        payload = {'kind': file_info['kind'], 'name': file_info['name']}
        put_data = str(payload).replace("'", '"')
        logging.debug(put_data)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'put', put_data = put_data)
        return result
    
    #----------------------------------------------------------------------
    def list(self):
        """NOT TESTED"""
        url = self.metadataUrl + '/trash'
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'get')
        return result
    
    #----------------------------------------------------------------------
    def restore(self, id):
        """NOT TESTED"""
        url = self.metadataUrl + '/trash/{id}/restore'.format(id = id)
        result = AmazonCloudDriveBase(LOGIN_DICT).send_request(url, refresh = True, method = 'post')
        return result


########################################################################
class ErrorLoginException(Exception):

    ''''''
    #----------------------------------------------------------------------

    def __init__(self, value):
        self.value = value
    #----------------------------------------------------------------------

    def __str__(self):
        return repr(self.value)

