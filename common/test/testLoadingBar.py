#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test script for LoadingBar class
#   test/testTable.py -v2
import time
#from TauFW.common.tools.log import Logger
from TauFW.common.tools.LoadingBar import LoadingBar

  
def main():
  step = 0.1 # sleep
  messages = ["lol", "lolbroek", "papey", "pop", "foobar", "barderman", "OMG", "domdomdom"]
  
  bar = LoadingBar(5)
  for i in range(0,8):
    time.sleep(step)
    bar.count()
  print ">>> Done with first loading bar."
  
  bar = LoadingBar(5,prepend=">>> Loading bar: ")
  for i in range(0,7):
    time.sleep(step)
    bar.count()
  
  bar = LoadingBar(20,width=17)
  for i in range(0,21):
    time.sleep(step)
    bar.count()
  
  bar = LoadingBar(steps=20,width=10,append=" Done!\n")
  for i in range(0,21):
    time.sleep(step)
    bar.count()
  
  bar = LoadingBar(17,width=23)
  for i in range(0,20):
    time.sleep(step)
    bar.count()
  
  bar = LoadingBar(10,width=30,remove=True)
  for i in range(0,10):
    time.sleep(step)
    bar.count()
  print ">>> Removed bar!"
  
  bar = LoadingBar(20,width=17,counter=True,append=" Done!\n")
  for i in range(0,21):
    time.sleep(step*3)
    bar.count()

  bar = LoadingBar(5,width=17,counter=True)
  for i in range(0,5):
    time.sleep(1)
    bar.count(messages[i])
  
  bar = LoadingBar(5,width=17,counter=True,remove=True)
  for i in range(0,5):
    time.sleep(step*3)
    bar.count(messages[i])
  print ">>> Removed bar again..."
  
  bar = LoadingBar(8,width=10,counter=True,append="Done.\n")
  for message in messages:
    time.sleep(step*3)
    bar.count(message)
  
  bar = LoadingBar(5,width=10,counter=True,append="Done.",remove=True)
  for i in range(0,5):
    time.sleep(step*3)
    bar.count(messages[i])
  print ">>> Removed bar again..."
  
  bar = LoadingBar(5,width=10,counter=True,append="Done.\n")
  for i in range(0,5):
    bar.message(messages[i])
    time.sleep(step*3)
    bar.count()
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test script for LoadingBar class"""
  parser = ArgumentParser(prog="testLoadingBar",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  print
  main()
  print
  
