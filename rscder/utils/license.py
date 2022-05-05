import base64
from Crypto.Cipher import AES
import uuid
import hashlib
import datetime

# 

class AESHelper(object):
    def __init__(self, password, iv):
        self.password = bytes(password, encoding='utf-8')
        self.iv = bytes(iv, encoding='utf-8')

    def pkcs7padding(self, text):
        """
        明文使用PKCS7填充
        最终调用AES加密方法时，传入的是一个byte数组，要求是16的整数倍，因此需要对明文进行处理
        :param text: 待加密内容(明文)
        :return:
        """
        bs = AES.block_size  # 16
        length = len(text)
        bytes_length = len(bytes(text, encoding='utf-8'))
        # tips：utf-8编码时，英文占1个byte，而中文占3个byte
        padding_size = length if(bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        # tips：chr(padding)看与其它语言的约定，有的会使用'\0'
        padding_text = chr(padding) * padding
        return text + padding_text

    def pkcs7unpadding(self, text):
        """
        处理使用PKCS7填充过的数据
        :param text: 解密后的字符串
        :return:
        """
        length = len(text)
        unpadding = ord(text[length-1])
        return text[0:length-unpadding]

    def encrypt(self, content):
        """
        AES加密
        模式cbc
        填充pkcs7
        :param key: 密钥
        :param content: 加密内容
        :return:
        """
        cipher = AES.new(self.password, AES.MODE_CBC, self.iv)
        content_padding = self.pkcs7padding(content)
        encrypt_bytes = cipher.encrypt(bytes(content_padding, encoding='utf-8'))
        result = str(base64.b64encode(encrypt_bytes), encoding='utf-8')
        return result

    def decrypt(self, content):
        """
        AES解密
        模式cbc
        去填充pkcs7
        :param key:
        :param content:
        :return:
        """
        cipher = AES.new(self.password, AES.MODE_CBC, self.iv)
        encrypt_bytes = base64.b64decode(content)
        decrypt_bytes = cipher.decrypt(encrypt_bytes)
        result = str(decrypt_bytes, encoding='utf-8')
        result = self.pkcs7unpadding(result)
        return result

def get_aes():
    # AES_SECRET和AES_IV分别为密钥和偏移量
    aes_helper = AESHelper(
        'ao234esorGFSFGubh#$^&@gihdfjl$@4', 
        'dergbdzbfdsdrt$g')
    return aes_helper

class LicenseHelper(object):
    def generate_license(self, end_date, mac_addr):
        print("Received end_date: {}, mac_addr: {}".format(end_date, mac_addr))
        psw = self.hash_msg('smartant' + str(mac_addr))
        license_str = {}
        license_str['mac'] = mac_addr
        license_str['time_str'] = end_date
        license_str['psw'] = psw
        s = str(license_str)
        licence_result = get_aes().encrypt(s)
        return licence_result
        
    def get_mac_address(self):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])
        
    def hash_msg(self, msg):
        sha256 = hashlib.sha256()
        sha256.update(msg.encode('utf-8'))
        res = sha256.hexdigest()
        return res
        
    def read_license(self, license_result):
        lic_msg = bytes(license_result, encoding="utf8")
        license_str = get_aes().decrypt(lic_msg)
        license_dic = eval(license_str)
        return license_dic
        
    def check_license_date(self, lic_date):
        current_time = datetime.datetime.strftime(datetime.datetime.now() ,"%Y-%m-%d %H:%M:%S")
        current_time_array = datetime.datetime.strptime(current_time,"%Y-%m-%d %H:%M:%S")
        lic_date_array = datetime.datetime.strptime(lic_date, "%Y-%m-%d %H:%M:%S")
        remain_days = lic_date_array - current_time_array
        remain_days = remain_days.days
        print('lic data:{}'.format(lic_date))
        print('remain_days: {}'.format(remain_days))
        if remain_days < 0 or remain_days == 0:
            return False
        else:
            return True
            
    def check_license_psw(self, psw):
        mac_addr = self.get_mac_address()
        hashed_msg = self.hash_msg('smartant' + str(mac_addr))
        if psw == hashed_msg:
            return True
        else:
            return False


if __name__ == '__main__':

    lic = LicenseHelper().generate_license('2022-12-31 00:00:00', LicenseHelper().get_mac_address())

    with open('license.lic', 'w') as f:
        f.write(lic[::-1])
    
    with open('license.lic', 'r') as f:
        license_result = f.read()[::-1]
    
    license_dic = LicenseHelper().read_license(license_result)

    print(license_dic)

    