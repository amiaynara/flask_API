try: 
    import unittest
    import requests
    import json
except: 
    print("Make sure you have app.py and unittest is installed".format(e))


class FlaskTest(unittest.TestCase):

    # Check for respose 200
    api_url = "http://localhost:5000"

    def test_index(self):
        response = requests.get(FlaskTest.api_url)
        self.assertEqual(response.status_code, 200)

    def test_signup(self):

        url = "http://localhost:5000/"

        payload={'user_name': 'noob',
        'passwd': 'noob'}
        headers = {
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        self.assertEqual(response.status_code, 200)
        jwt = response.headers['x-access-token']
        '''
        jwt = ""
        for i in token:
            if i == '{' or i=='}' or i=='\n' or i=='"' or i==" ":
                pass
            else:
                jwt +=i
        jwt = jwt.split(":")[-1]    
        print("the jwt is :", jwt)
        '''
        url = "http://localhost:5000/upload"
        filereader = open('/home/tesla/Pictures/Wallpapers/bitmap.png','rb')
        payload={}
        files=[
          ('file',('bitmap.png', filereader,'image/png'))
        ]
        headers = {
        }
        headers['x-access-token'] = jwt

        message = "Limit exceeded 5/min allowed"
        for i in range(7):
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            self.assertEqual(response.status_code, 200, message)
            print("Post request no: ", i, " successfull ....", "Response Status code : ", response.status_code)
            print("\n")
        filereader.close()



                

    
        

if __name__ == "__main__":
    unittest.main()
