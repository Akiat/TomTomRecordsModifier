#!/usr/bin/env python

import re
import sys
import binascii

def get_label(next_label_pos):
    label_len = int(hexRepr[next_label_pos-2:next_label_pos], 16) - 0x1b
    label = hexRepr[next_label_pos:next_label_pos + (label_len*2)].decode('hex')
    new_label_pos = next_label_pos + (label_len*2) + 2
    return (label, next_label_pos), new_label_pos

def get_locations():
    regex = re.compile("0400..0000000400..0000000800") #locations header

    locations = {}

    for i, res in enumerate(regex.finditer(hexRepr)):
        end = res.end()
        #Get coord with this format: first_set = ((latitude, offset), (longitude, offset))
        first_set = ((hexRepr[end:end+8], end), (hexRepr[end+8:end+16], end+8)) #actual position
        second_set = ((hexRepr[end+20:end+28], end+20), (hexRepr[end+28:end+36], end+28)) #nearest road

        next_label_pos = end+38
        first_label, next_label_pos = get_label(next_label_pos)
        second_label, next_label_pos = get_label(next_label_pos)
        third_label, next_label_pos = get_label(next_label_pos)

        locations[i] = [first_set, second_set, first_label, second_label, third_label]
        print '{} - {} - {} - {}'.format(i, first_label[0], second_label[0], third_label[0])

    return locations

def ask_record_to_modify(locations):
    location = None
    x = raw_input('Enter the index of coordinates you want to modify: ')
    while 42:
        try:
            location = locations[int(x)]
            print "------------------ RECORD TO MODIFY --------------------"
            print "0 = Actual position as ((latitude, offset_in_file), (longitude, offset_in_file))"
            print "1 = Nearest road as ((latitude, offset_in_file), (longitude, offset_in_file))"
            print "2 = Label part 1"
            print "3 = Label part 2"
            print "4 = Label part 3"
            print "--------------- CHOOSE PART TO MODIFY ------------------"
            break
        except (KeyError, ValueError):
            x = raw_input('Incorrect index: Enter the index of coordinates you want to modify: ')
    return location

def ask_part_to_modify(location):
    for i, res in enumerate(location):
        print i, res

    part = None
    lat_long = False
    x = raw_input('Enter the index of part you want to modify: ')
    while 42:
        try:
            part = location[int(x)]
            print "------------------- PART TO MODIFY ----------------------"
            print part
            break
        except (IndexError, ValueError):
            x = raw_input('Incorrect index: Enter the index of part you want to modify: ')
    if int(x) < 2:
        lat_long = True
    return part, lat_long, x

def modify_part(part, lat_long, filename):

    latitude = None
    longitude = None
    res = None
    if lat_long == True:
        while 42:
            latitude = raw_input("Enter latitude as 4 hex byte (0A1B2C3D):")
            longitude = raw_input("Enter longitude as 4 hex byte (0A1B2C3D):")
            if len(latitude) == 8 and len(longitude) == 8:
                break

    else:
        while 42:
            res = raw_input("The new one cannot exceed the length of the old ("\
                                + str(len(part[0])) + "), enter the new one: ")
            if len(res) <= len(part[0]):
                break

        res_spaced = res
        while len(res_spaced) < len(part[0]):
            res_spaced += ' '

    with open(filename, 'r+b') as f:
        if lat_long == True:
            f.seek(part[0][1]/2)
            f.write(binascii.unhexlify(latitude))
            f.seek(part[1][1]/2)
            f.write(binascii.unhexlify(longitude))
            part = ((latitude, part[0][1]),(longitude, part[1][1]))
            print 'WRITE `{}` AT THE OFFSET {}'.format(latitude, str(part[0][1]/2))
            print 'WRITE `{}` AT THE OFFSET {}'.format(longitude, str(part[1][1]/2))
        else:
            f.seek(part[1]/2)
            f.write(res_spaced)
            part = (res_spaced, part[1])
            print 'WRITE `{}` AT THE OFFSET {}'.format(res, str(part[1]/2))

    print '-------------------- CHANGES SAVED ----------------------'
    return part

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print 'Usage: ./modifyRecords.py YourMapSettings.cfg'
        sys.exit(0)

    try:
        with open(sys.argv[1], 'rb') as f:
            content = f.read()
            hexRepr = binascii.hexlify(content)
    except IOError as e:
        print e
        print 'Exiting...'
        sys.exit(0)

    locations = get_locations()
    location = ask_record_to_modify(locations)
    while 42:
        part, lat_long, num = ask_part_to_modify(location)
        part = modify_part(part, lat_long, sys.argv[1])
        location[int(num)] = part
        if raw_input("Modify another part of this record ? (y/n) ") != 'y':
            break
    print 'Exiting.'
