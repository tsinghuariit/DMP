# -*- coding: utf-8 -*-
# coding=utf-8
__author__ = 'ruidong.wang@tsingdata.com'

import random, string



poolOfChars  = string.ascii_letters + string.digits
random_codes = lambda x, y: ''.join([random.choice(x) for i in range(y)])

class LengthError(ValueError):
   def __init__(self, arg):
      self.args = arg

def pad_zero_to_left(inputNumString, totalLength):
    '''
    takes inputNumString as input,
    pads zero to its left, and make it has the length totalLength
    1. calculates the length of inputNumString
    2. compares the length and totalLength
        2.1 if length > totalLength, raise an error
        2.2 if length == totalLength, return directly
        2.3 if length < totalLength, pads zeros to its left
    '''
    lengthOfInput = len(inputNumString)
    if lengthOfInput > totalLength:
        raise LengthError("The length of input is greater than the total\ length.")
    else:
        return '0' * (totalLength - lengthOfInput) + inputNumString



def invitation_code_generator(start,quantity, lengthOfRandom, LengthOfKey):
    '''
    generate `quantity` invitation codes
    '''
    placeHoldChar = "L"
    for index in range(start,start+quantity):
        tempString = ""
        try:
            yield random_codes(poolOfChars, lengthOfRandom) + placeHoldChar + \
                pad_zero_to_left(str(index), LengthOfKey)
        except LengthError:
            print "Index exceeds the length of master key."

if __name__ == '__main__':
    for invitationCode in invitation_code_generator(100,100, 15, 5):
        print invitationCode
