import hashlib
import sys

def makePass(passw):
#	passw = sys.argv[1]

# Initializing the sha256() method
	sha256 = hashlib.sha256()

# Passing the byte stream as an argument
	sha256.update(passw.encode(encoding="UTF-8"))

# sha256.hexdigest() hashes all the input data
# passed to the sha256() via sha256.update()
# Acts as a finalize method, after which all
# the input data gets hashed
# hexdigest() hashes the data, and returns
# the output in hexadecimal format
	string_hash = sha256.hexdigest()
	
	return string_hash

