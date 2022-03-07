import numpy as np
import json 
import random
import itertools

# Generate artificial query of size n
def generate_data(file_name,r1,r2):
    """
        Function to generate query data for the smart contract with n queries over r range of study id.

        Parameters:
            file_name (str): Name of the file where we want to store the query data.
            r1,r2 (int): The range of study ids (e.g. 1-15)

        Output:
            file_name.txt (str): The query data file name.
        """

    # the preference options
    preferenceNames = {}
    preferenceNames[0] = "DEMOGRAPHICS"
    preferenceNames[1] = "MENTAL_HEALTH"
    preferenceNames[2] = "BIOSPECIMEN"
    preferenceNames[3] = "FAMILY_HISTORY"
    preferenceNames[4] = "GENETIC"
    preferenceNames[5] = "GENERAL_CLINICAL_INFORMATION"
    preferenceNames[6] = "SEXUAL_AND_REPRODUCTIVE_HEALTH"

    # open a (new) file to write in
    file = open(file_name, "w")
    # all possible combinations 
    lst = list(itertools.product([0, 1], repeat=7))
    lpref = []
    for i in lst:
        lpart = []
        count = 0
        for j in i:   
            if(j == 1):
                lpart.append(preferenceNames[count])
            count = count + 1
        lpref.append(lpart)
    

    # write the queries to the file in json format line by line
    for i in range(r1, r2+1):
        for j in lpref:
            temp = {}
            study_id = i
            temp["study_id"] = study_id
            temp["requested_site_preferences"] = j
            #print(temp)
            json.dump(temp, file)
            file.write("\n")
    
    file.close()

    # print
    print("queries saved to given file")

# use the above function to generate queries 
f = "query.txt"
r1 = 1
r2 =15

generate_data(f,r1,r2)

