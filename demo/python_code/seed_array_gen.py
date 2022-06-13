seedLength = 100
# seedFileName = "../seed_array" + "_" + str(seedLength) + ".txt"
seedFileName = "../seed_array.txt"
seedFile = open(seedFileName, "w")
for line in range(seedLength):
    seedFile.write("%s" % line)
    if line != range(seedLength)[-1]:
        seedFile.write("\n")
seedFile.close()
