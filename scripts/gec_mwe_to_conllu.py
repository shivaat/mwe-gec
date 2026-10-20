import argparse

'''
This script reads the lines of the GEC data that is annotated for MWEs (with _[B and _[I labels)
and write them in PARSEME .conllu (.cupt) format file.
'''

def gec_mwe_to_conllu(input_path, output_path):

    first_line = "# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC PARSEME:MWE"

    with open(output_path, 'w') as o:
        
            
        o.write(first_line+"\n")
        with open(input_path) as f:
                embedded = 0                        
                for line in f:
            
                    o.write("# text = "+line)
                    counter = 0
                    i = 1
                    for w in line.split():
                        if "_[B-" in w:  #w.endswith("_[B-X]"):
                            b = 1
                            counter+=1
                            category = w.split("_[B-")[-1][0:-1]
                            if category == "X":
                                category = "I"
                            tag = str(counter)+":"+category
                            w_ = w.split("_[B-")[0]
            
                        elif "_[I-" in w:    # w.endswith("_[I-X]"):
                            tag = str(counter)
                            w_ = w.split("_[I-")[0]

                        elif "_[b-" in w:       # I might decide to take these into consideration
                            tag = "*"           # since Parseme .cupt can handle embedded cases
                            w_ = w.split("_[b-")[0]
                            embedded += 1
                        elif "_[i-" in w:
                            tag = "*"
                            w_ = w.split("_[i-")[0]
        
                        else:
                            tag = "*"
                            w_ = w
                        row_list = [str(i), w_] + ["_"]*4 + ["0"] + ["_"]*3 + [tag]
                        o.write("\t".join(row_list)+"\n")
                        i+=1
                    o.write("\n")

                print("Number of embedded:", embedded)    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run gec_mwe_to_conllu with input and output paths."
    )
    parser.add_argument("-i", "--input", required=True, help="Path to the input file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output file")

    args = parser.parse_args()

    gec_mwe_to_conllu(args.input, args.output)

