from workunit import Workunit, WorkunitProvider

provider = WorkunitProvider()


#print "pending:", workunits_pending
#print "finished:", workunits_finished

print "Pending", len(provider.workunits_pending)
total, finished = provider.get_progress()

print "%d / %d (%2.2f%%)" % (finished, total, finished * 100.0 / total)

print "Keys found:"
patterns = [
"316c59a457b57f3b".decode("hex"), 
"75e6182ad2bf6769".decode("hex"), 
"06DE6FF356237359".decode("hex"),   # firmware.asic
"59732356F36FDE06".decode("hex"),  # firmware.asic mirrored

"0D3D6820F74FD4D5".decode("hex"),  # firmware asic 2
"d5d44ff720683d0d".decode("hex"),  # firmware asic 2 mirrored WOW
"ab7fed84d3a248eb".decode("hex"),  # triforce
"58135fa988530df5".decode("hex"), 

"7a9f54ea665bb5eb".decode("hex"), 
"2ace976739f9e504".decode("hex"), 
#"8411c2805a921225".decode("hex"), 
"74870d121facfc0d".decode("hex"), 
"4150da72c246f074".decode("hex"), 

"68a6209afe7580c2".decode("hex"),  # triforce
"0951e7519fb81f24".decode("hex"),  # r
"00210a3e9ea7502d".decode("hex"), 
"f004db5b605f2f89".decode("hex"),  # test 3

]
for wu in provider.workunits_finished_interesting:
  if wu.results:
    for key in wu.results:
      print key.encode("hex")
      for r in patterns:
        from Crypto.Cipher import DES
        print "\t", DES.new(key).decrypt(r).encode("hex"), r.encode("hex")
