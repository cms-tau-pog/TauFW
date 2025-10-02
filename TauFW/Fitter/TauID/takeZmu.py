year="UL2018"
jobdir='./log'
for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
       for pt in ["20to25", "25to30", "30to35", "35to40", "40to50", "50to70", "70to2000"] :
       print(wp)
       #for dm in ['dm0','dm1', 'dm10', 'dm11']:
           print(dm)
           file = open(jobdir + '/ztt_'+wp+'_'+year+'_pt'+pt+'.log')
           #file = open(jobdir + '/ztt_'+wp+'_'+year+'_'+dm+'.log')
           for line in file:
               line = line.rstrip()
               words = line.split()
               if line.find('ZTT_mu')!=-1:
                  val = float(words[2])
                  #print("WP: "+ wp + ", pT:"+pt+", Val=" + str(val))
                  print(val)


       print(' ')
       print(' ')
       print(' ')
       print(' ')
