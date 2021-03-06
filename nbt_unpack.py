#!/usr/bin/python

VERSIONSTRING = 'BMW NBT and NBT-Evo unpacker by 2real4u v0.01'

from sys import argv, exit
import os

META_HEADER_ID = "\x02"
META_FOOTER_ID = "\x04", "\x03"
FILEHEADER = "\x01\x01\x00\x01\x00\x00\x00\x01\x00\x01"
META_HEADER_LEN = 9 # Including ID
META_FOOTER_LEN = 9 # Including ID

create_folders = True
write_meta = True
debug = True


print ("\n"+VERSIONSTRING)

from binascii import hexlify, b2a_hex

def bytes2int(bytestring): # Convert from raw hex to int
 return int(b2a_hex(bytestring[::-1]), base = 16)

if len(argv) != 2:
 
 print("\nUsage: " + argv[0].split("\\")[-1] + " filename")
 exit(1)

file_object=open(argv[1],"rb")

def get_input_file(startaddress,endaddress=0):
 if endaddress==0: endaddress=startaddress+1
 if debug: print ("read_start_address="+format(startaddress,'02x')+" read_end_address="+format(endaddress,'02x'))
 file_object.seek(startaddress)
 return file_object.read(endaddress-startaddress)
 
if get_input_file(0,len(FILEHEADER)) != FILEHEADER:
 print("\nUnknown file format")
 exit(1)
 

ifs_counter = 0000 # This will hold the .ifs filename suffix
efs_counter = 0000 # This will hold the .ifs filename suffix

current_position = 0x0a # Current position in file

while True:

 meta_header_position = current_position
 if debug: print("Found meta header at 0x" + format(meta_header_position,'02x') + "\n")
 if meta_header_position == -1: break # Can't find header? Quit loop

 meta_len = bytes2int(get_input_file(meta_header_position + 3,meta_header_position + 5)) # Looks like meta blob length is in one byte
 if debug: print("Meta length 0x" + format(meta_len,'02x') + "\n")

 meta_blob_start_position = meta_header_position + META_HEADER_LEN
 meta_blob_end_position = meta_blob_start_position + meta_len

 meta_blob = (get_input_file(meta_blob_start_position, meta_blob_end_position)) # Here we extract the meta blob
 meta_items = meta_blob.split(";") # Split blob into separate x=y lines

 if debug: print("Meta blob end position at 0x" + format(meta_blob_end_position,'02x') + "\n")

 meta_dict = {}
 is_ifs = False
 is_efs = False
 for item in meta_items[0:len(meta_items)-1] : # Convert list of x=y into dictionary
  item_name = item.split("=")[0]
  item_value = item.split("=")[-1]
  meta_dict[item_name] = item_value
  if item_name == "FsImageType" and item_value == "IFS" : is_ifs = True # This header is for IFS image
  if item_name == "FsImageType" and item_value == "EFS" : is_efs = True # This header is for IFS image
 if is_ifs:
  filename = "image" + str(ifs_counter).zfill(4) + ".ifs"
  ifs_counter += 1
 elif is_efs:
  filename = "image" + str(ifs_counter).zfill(4) + ".efs"
  efs_counter += 1
 elif "Name" in meta_dict:
  filename = meta_dict["Name"]
 elif "Tag" in meta_dict:
  filename = meta_dict["Tag"]
 else:
  filename = "Unknown"
 meta_filename = filename + ".META"

 filepath = "./"+meta_dict["CPU"]

 if create_folders and "TargetPath" in meta_dict:
  filepath += meta_dict["TargetPath"]
 elif create_folders:
  filepath += "/"
 else :
  fileapath=""
 if write_meta:
  try: 
   os.makedirs(filepath)
  except: pass
  with open(filepath+meta_filename,"w") as out_file: 
   out_file.write("\n".join(meta_items))


 if get_input_file(meta_blob_end_position, meta_blob_end_position+1) in META_FOOTER_ID : # Check if we have a header or footer after meta
  write_file = True
  meta_footer_position = meta_blob_end_position + 1
  if debug: print("Found meta footer at 0x" + format(meta_footer_position,'02x') + "\n")
  file_start_position = meta_footer_position + META_FOOTER_LEN - 1
  if debug: print("Found file chunk start at 0x" + format(file_start_position,'02x') + "\n")

  file_len_raw = get_input_file(meta_footer_position + 2, meta_footer_position + 6)
  file_len = bytes2int(file_len_raw)+1 # Looks like meta blob length is in three bytes
  if debug: print("File chunk length 0x" + format(file_len,'02x') + "\n")
  file_end_position = file_start_position + META_FOOTER_LEN + file_len -10
  if debug: print("File chunk end found at 0x" + format(file_end_position,'02x') + "\n")
  current_position = file_end_position
  if debug: print("Current position 0x" + format(current_position,'02x') + "\n")
 else:
  write_file = False
  current_position = meta_blob_end_position
  if debug: print("Current position 0x" + format(current_position,'02x') + "\n")
 if write_file:
  print (filepath+filename)
  try:
   os.makedirs(filepath)
  except: pass
  with open(filepath+filename,"wb") as out_file:

   out_file.write(get_input_file(file_start_position, file_end_position))
 if current_position == os.stat(argv[1]).st_size:
  print ("End of file!")
  break

 while get_input_file(current_position) in META_FOOTER_ID: # Check if we have another chunk
  write_file = True
  meta_footer_position = current_position+1
  if debug: print("Current position 0x" + format(current_position,'02x') + "\n")
  if debug: print("Found chunk footer at 0x" + format(meta_footer_position,'02x') + "\n")
  file_start_position = meta_footer_position + META_FOOTER_LEN - 1
  if debug: print("Found file chunk start at 0x" + format(file_start_position,'02x') + "\n")

  file_len_raw = get_input_file(meta_footer_position + 2, meta_footer_position + 6)
  file_len = bytes2int(file_len_raw)+1 # Looks like meta blob length is in three bytes
  if debug: print("File chunk length 0x" + format(file_len,'02x') + "\n")
  file_end_position = file_start_position + META_FOOTER_LEN + file_len -10
  if debug: print("File chunk end found at 0x" + format(file_end_position,'02x') + "\n")
  current_position = file_end_position
  with open(filepath+filename,"ab") as out_file:
   out_file.write(get_input_file(file_start_position, file_end_position))

  
 if debug: print("="*79 + "\n")


 
 
 
 