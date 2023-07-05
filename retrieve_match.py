import csv
import os
import re
import time

image_extension = (".jpg", ".png",".svg","jpeg")

def get_autographes( csv_source : str ) -> list[str]:
    csv_data = []
    with open(csv_source, newline='') as inputfile:
        return [row[9] for row in csv.reader(inputfile)]
        #csv_data = [row for row in csv.reader(inputfile)]

    """BMDV_name_convention = 'BMDV-ms'
    autographes = [ i[9] for i in csv_data if i[9].startswith(BMDV_name_convention) ]
    return autographes"""

def fetch_images(directory : str, recursive : bool=True) -> list[str] :
    images_files=[]
    for (dirpath, dirnames, filenames) in os.walk(directory):
        images_files.extend([f for f in filenames if f.lower().endswith(image_extension)])
        if not recursive :
            break
    return images_files


def get_matches( autographes : list[str], images_files : list[str]) -> tuple[int,dict,dict]:


    # Create the dictionnary of {cote:autographe}
    cotes = {}
    for letter_name in autographes :
        #print(letter_name, end=" | ")
        cote = ""
        for numbers in re.findall(r"(\d+(?:-\d+)*(?:bis+)*(?: bis+)*(?:ter+)*(?: ter+)*)", letter_name):
            # Concatenate every cote from the same letter
            if cote != "" :
                cote+= "+"
            cote+=numbers
        cote =cote.replace(" ","")
        if cote != "" :
            cotes[cote] = letter_name
            #print(cote +"  ->  "+ letter_name)

    count = 0
    cotes_availables = {}
    files = sorted([i for i in images_files if i.lower().startswith("ms")])
    current_size = len(files)
    i = 0
    # To find matches more efficiently, we remove images already associated
    while i < current_size :
        # Loop though each cote_group (some letter have 2 cotes)
        
        for cote_group in cotes.keys() :  
            for cote in cote_group.split("+") :
                
                filename = files[i].lower()
                for cote_in_name in re.findall(r"(\d+(?:-\d+)*(?:bis+)*(?: bis+)*(?:ter+)*(?: ter+)*)", filename) :
                    #if "251" in filename :
                    print(filename+">> "+cote_in_name + " ==? "+ cote )
                    if cote== cote_in_name.replace(" ","") :
                        print("FOUND")
                        #print(filename+">> "+cote_in_name)
                        
                        if cote not in cotes_availables :
                            print("went in")
                            cotes_availables[cote] = []
                        cotes_availables[cote].append(files[i])
                        count+=1
                        del files[i]
                        print("del" + files[i])
                        current_size-=1
                        i = 0
                        break # ERROR HERE NEED TO BREAK TILL WHILE
                
                #print(filename+" || " + cote_group)
        else : 
            i+=1
    return count,cotes, cotes_availables


def get_length_list_dict(dictionnary : dict) ->int :
    length = 0
    for item in dictionnary.values() :
        length+= len(item)
    return length

#print (get_length_list_dict(cotes_availables))

# Dictionnaire
# cotes : [ code : nom complet de l'autographe ]
# cotes_available : [ code : [ liste des noms de fichiers images ]]

if __name__ == "__main__" :

    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    autographes = get_autographes(csv_source)

    if os.path.exists("result.txt"):
        os.remove("result.txt")
    for dir in [1] : 
    #for dir in next(os.walk('Images'))[1] :
        #1620-49-49ges_dir = "Images/"+dir
        #path_images_dir = "Images/Ms 1620-3.jpg"
        path_images_dir = "Images/rest"

        images_files = fetch_images(path_images_dir, True)
        print("Pour le dossier > "+path_images_dir)
        print("total img > "+ str(len(images_files)) + "| start timer ")
        start_time =time.time()
        foundNB,cotes,cotes_associated = get_matches(autographes,images_files)
        for i in cotes.items() :
            #print(i)
            pass

        print("Correspondance trouvé : > " + str(foundNB) + " | Temps pris : "+ str(time.time() - start_time))
        print("--------------------")

        with open("result.txt", 'w') as f:
            for i in cotes_associated.items() :
                #f.write(str(i)+"\n")
                f.write(str(i[0])+";"+str(i[1])+"\n")
                print(str(i[0])+";"+str(i[1]))

        for i in cotes :
            #print(i)
            pass
