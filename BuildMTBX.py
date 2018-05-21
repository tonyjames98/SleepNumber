import sys


test_name = sys.argv[1]
# Important note: Path passed from Jenkins needs to replace \ with \\ to ensure it is passed correctly
path = sys.argv[2]
test_suite = sys.argv[3]
print(test_name)
print(path)
print(test_suite)


mtbx_file = open("TestMTBX.mtbx",'w')

mtbx_file.write('<Mtbx>\n')

mtbx_file.write('<Test name = "%s" path="%s" >\n'
                %(test_name,path))

mtbx_file.write('\t<Parameter name="TestSuite" value="%s" type="string"/>\n'
                %(test_suite))

mtbx_file.write('</Test>\n')

mtbx_file.write('</Mtbx>\n')

mtbx_file.close()