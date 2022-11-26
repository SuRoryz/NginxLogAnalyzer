import binascii
from datetime import datetime

class Parser:
    @staticmethod
    def parse(line, server=None):
        def is_hex(s):
            s = s.replace('"', '').replace("'", "")
            return len(repr(s)) > len(s) + 2

        def _check_warns(field):
            return is_hex(field)

        result = {}
        splitted = line.split()

        result["warn"] = False
        result["remote_addr"] = splitted[5]
        result["remote_user"] = splitted[7]
        result["time"] = datetime.strptime(splitted[8], "[%d/%b/%Y:%H:%M:%S")
        result["request_method"] = splitted[10].strip('"')
        result["request_url"] = splitted[11].strip('"')
        result["resuest_protocol"] = splitted[12]
        result["request_status"] = splitted[13]
        try:
            result["request_size"] = int(splitted[14])
        except:
            result["warn"] = True
        result["http_reffer"] = splitted[15].strip('"')
        result["user_agent"] = " ".join(splitted[16:]).strip('"')

        if server:
            result["server"] = server
        
        for key in result:
            if key in ["time", "request_size", "warn"]:
                continue

            if _check_warns(result[key]):
                result["warn"] = True
                print(result[key])
                return result

        return result

#print(Parser.parse('''66.249.65.159 - - [06/Nov/2014:19:10:38 +0600] "GET /news/53f8d72920ba2744fe873ebc.html HTTP/1.1" 404 177 "-" "Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"'''))



