import sys
import os
import json
import errant


'''
This script is for adding mwe edits to m2 files, for the purpose of evaluating GEC
while considering MWE edits. MWE edits are added when MWE tags overlap with GEC errors.
 
The function get_sentences_with_tags(mwe_tagged_file, without_tags_file) employs the MWE tags of the 
same file and just convert the representation
The function get_sentences_with_mapped_tags(mwe_tagged_file, without_tags_file, other_file) gets the MWE tags 
from a parallel corresponding file and use the alignments to apply it to the new file.
'''

# Input: An annotated sentence with MWE markup
# Output: A list of token index spans and type for each MWE: [(2, 4, type), ...] 
def extract_mwe_ids(sent):
    '''
    - This code considers single-token and discontuous MWEs as well
    - Extracts only verbal MWEs
    '''
    # Strip whitespace and split into tokens
    toks = sent.strip().split()
    # Get the ids of all tokens containing MWEs using _; e.g. Depending_[B-P] on_[I-P]
    all_ids = [i for i in range(0, len(toks)) if "_" in toks[i]]
    # Return an empty list if there are no ids
    if not all_ids:
        return []
    # Otherwise, split the ids into spans
    else:
        split_ids = []
        # Loop through token ids
        mwes = {}   # the key for an MWE dict is a tuple of the MWE type and the begining token index
        for i in range(len(toks)):          
            if "_" in toks[i]:
                type = toks[i].split("_")[-1].split("-")[-1][:-1]
                if toks[i].split("_")[-1].startswith('[B-'):
                    # the key for an MWE dict is a tuple of the MWE type and the begining token index
                    # the value is the list of the indices of all tokens belonging to that MWE
                    mwes[(type,i)] = []
                elif toks[i].split("_")[-1].startswith('[I-'):
                    key_tup = ()
                    # loop though mwes to find the key tuple which this I- token belongs to 
                    for m in mwes:
                        if type == m[0]:
                            key_tup = m
                    if key_tup:
                        mwes[key_tup].append(i)

            ''' 
            # First span begins
            if i == 0: split_ids.append([all_ids[i]])
            # If the next token is in the span, add it to the current span
            if all_ids[i+1] == all_ids[i] + 1: split_ids[-1].append(all_ids[i+1])
            # Otherwise, start a new span
            else: split_ids.append([all_ids[i+1]])
            '''
        # Convert the spans into a list of (start, end, type) tuples
        spans = []
        for m in mwes:
            #if m[0].startswith('V'):   # At some point, I decided to tag for all types of MWEs
                if len(mwes[m]):
                    spans.append((m[1], max(mwes[m])+1, m[0]))
                else:
                    spans.append((m[1], m[1]+1, m[0]))

        return spans

def get_sentences_with_mapped_tags_return_m2_edits(mwe_tagged_file, without_tags_file, other_file, m2_file):
    '''
    This function  reads the MWE tags of the error-corrected file,
    map them back to the original file and
    return the new mwe-added m2 edits.
    
    mwe_tagged_file: .txt file tagged with MWEs
    without_tags_file: .txt file (cor/orig) without MWEs
    other_file: .txt file of the other side (orig/cor)
    m2_file: the original m2 file 
    '''
    annotator = errant.load('en')
    new_sentences = []
    new_sentences_cor = []
    count = 0
    corrected = 0

    m2 = m2_file.read().strip().split("\n\n")
    # Output M2 file
    #out = open('test.m2', "w")
    m2_edits = []

    sent_count = 0
    # Loop through sentences
    for line1, line2, line3 in zip(mwe_tagged_file, without_tags_file, other_file):
        # Extract MWE ids and types from the corrected side
        c_mwe_ids = extract_mwe_ids(line1)

        # Get the original, corrected and edits from the M2 block
        o_sent, _, edits= process_m2(m2[sent_count])
        # Add orig sentence to the output M2
        #out.write(" ".join(["S"]+o_sent)+"\n")
        m2_edits.append(" ".join(["S"]+o_sent)+"\n")
        # Add a dummy edit if there are no edits
        if not edits:
            #out.write("A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||"+"0"+"\n")
            m2_edits.append("A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||"+"0"+"\n")
        # List of new MWE edits
        new_edits = []

        orig = annotator.parse(line3)
        cor = annotator.parse(line2)
        alignment = annotator.align(orig, cor)

        orig = [str(w) for w in orig]
        cor = [str(w) for w in cor]
        line2 = line2.strip().split()

        new_sent_cor = []
        cur_cor = 0

        new_sent = []
        if len(c_mwe_ids):
            mwe_mappings = []
            cur = 0
            for mwe in c_mwe_ids:
                # each mwe is a tuple of two numbers: the begining and the end indices of a mwe  
                # in the corrected sequence
                
                # First, we easily prepare the correct side itself
                # We can decide to add that only if we find alignment on the other side as well
                # But for now we add it
                b_cor = mwe[0]
                e_cor = mwe[1]
                m_type = mwe[2]
                #new_sent_cor.extend(line2[cur_cor:b_cor] + ['[MWE]'] + line2[b_cor:e_cor] + ['[/MWE]'])
                new_sent_cor.extend(line2[cur_cor:b_cor] + ['['+m_type+']'] + line2[b_cor:e_cor] + ['[/'+m_type+']'])
                cur_cor = e_cor

                # Second, we prepare the orig side by mapping back the MWEs
                b = -1
                e = -1
                temp_b = -1
                temp_e = -1
                # Loop through the alignments
                for a in alignment.align_seq:
                    # each a in alignment.align_seq is in the form of: 
                    # ("A LETTER", O_indx_b, O_indx_e, T_indx_b, T_indx_e)
                    
                    # if the token in target side of alignment a is the exact token  of MWE span
                    if mwe[0] == a[3] and a[1]==a[2]:  
                        if b==-1:   # if the begining has not yet be found:
                            temp_b = a[1]
                            temp_e = a[1] # This is quite hacky, but just because when we addin the end, we do e+1

                    # if the token in target side of alignment a is one of the tokens among the tokens of MWE span
                    if (mwe[0] == a[3] or (a[3]>mwe[0] and a[3]<mwe[1])) and a[3]!=a[4] and a[1]!=a[2]:  
                                    # a[1]==a[2] or a[3]==a[4] means no alignment in the orig or cor corresponsingly 
                        if b==-1:   # if the begining has not yet be found:
                            b = a[1]
                            e = a[1] #+ 1
                        if a[1]<b:  
                            b = a[1]
            
                    # if the token in the target side of the alignment is equal the ending of the MWE
                    if mwe[1]-1 == a[3] and a[3]!=a[4] and a[1]!=a[2]:  
                        if b==-1:       # b might still be -1 when for any reason begining token of MWE is not aligned to anything
                            b = a[1]
                            e = a[1] 
                        if e==-1 or a[1]>e:  # This is the main condition that sets the ending
                            e = a[1] 

                    # If b is already set, and the MWE goes over the alignment. Meaning that the token
                    # should be part of the MWE
                    if mwe[0] == b and mwe[1]-1 > a[3]:
                        e = a[1] #+ 1
                    
                if b == -1 or e == -1:  # This is only for the case we had Missing MWE, which cause both above conditions to be missed
                    b = temp_b
                    e = temp_e-1
                    #print("Missing: The begining of MWE is not set correctly! So they are reset", ((b,e), (mwe[0], mwe[1])))
                    if temp_b == -1:
                        print("Warning: b and e are still -1", ((b,e), (mwe[0], mwe[1])))
                mwe_mappings.append(((b,e+1), (mwe[0], mwe[1])))
            
                count += 1
                # Count the number of MWE corrections
                if cor[mwe[0]:mwe[1]] != orig[b:e+1]:   # whwn there is a difference between the expressions in the alignments (i.e. error)
                    corrected+=1
                    print('ALIGNMENT: ',orig[b:e+1], '->', cor[mwe[0]:mwe[1]])
                    
                    # Add as a new MWE error only if the alignmet is not just changing upper case to lower case or the reverse
                    if " ".join(orig[b:e+1]).lower() != " ".join(cor[mwe[0]:mwe[1]]).lower():
                        # Add them to the edits for m2, Edits in the Format:
                        # [cat, o_start, o_end, o_str, c_start, c_end, c_str]
                        if b == e+1:
                            # Missing: if there is no alignment in the orig (begining index == end index)
                            new_edits.append(["M:MWE_"+mwe[2], str(b),str(e+1), str(orig[b:e+1]), str(mwe[0]),
                                            str(mwe[1]), " ".join(cor[mwe[0]:mwe[1]])])
                        else:
                            new_edits.append(["R:MWE_"+mwe[2], str(b),str(e+1), str(orig[b:e+1]), str(mwe[0]), 
                                            str(mwe[1]), " ".join(cor[mwe[0]:mwe[1]])])

                if len(orig[b:e+1]):  # when there is no equivalent in orig, Missing error.
                    #new_sent.extend(list(orig[cur:b]) + ['[MWE]'] + list(orig[b:e+1]) + ['[/MWE]'])
                    new_sent.extend(list(orig[cur:b]) + ['['+mwe[2]+']'] + list(orig[b:e+1]) + ['[/'+mwe[2]+']'])

                    # If we decide to add the tags only if equivalents are found in the orig side 
                    #new_sent_cor.extend(line2[cur_cor:b_cor] + ['[MWE]'] + line2[b_cor:e_cor] + ['[/MWE]'])
                    #cur_cor = e_cor

                else:
                    # Ideally in this case we shouldn't have MWE tags in the corrected side either
                    print('WARNING: No alignment found for the MWE', b, e+1, "c_mwe_ids", c_mwe_ids)
                    #print('\t orig:', orig, alignment.align_seq)
                cur = e +1 
            new_sent.extend(orig[cur:])
            new_sentences.append(" ".join(new_sent))

            new_sent_cor.extend(line2[cur_cor:])
            new_sentences_cor.append(" ".join(new_sent_cor))
        else:
            new_sentences.append(line3.strip())
            new_sentences_cor.append(" ".join(line2))

        final_edits = []
        # To traverse the edits
        cur = 0
        flag = 0
        # Loop through original edits
        for i in range(cur, len(edits)):

            if "SPELL" in edits[i][0]: # We don't want to consider SPELL errors as MWEs
                # An MWE error might have been added that already contain the spell error
                # We add the original SPELL error if it is the 1st error, or it doesn't have overlap
                # with the previously added error
                if len(final_edits)==0 or (len(final_edits) and not edits[i][1]<int(final_edits[-1][2])):
                    final_edits.append(edits[i])
                continue

            ##### Ignoring the following error types as they are not MWE-related errors
            if "VERB:SVA" in edits[i][0]:   # We do not want to consider this as MWEs!
                if len(final_edits)==0 or (len(final_edits) and not edits[i][1]<int(final_edits[-1][2])):
                    final_edits.append(edits[i])
                continue
            if "NOUN:NUM" in edits[i][0]:   # We do not want to consider this as MWEs!
                if len(final_edits)==0 or (len(final_edits) and not edits[i][1]<int(final_edits[-1][2])):
                    final_edits.append(edits[i])
                continue
            if "VERB:TENSE" in edits[i][0]:   # We do not want to consider this as MWEs!
                if len(final_edits)==0 or (len(final_edits) and not edits[i][1]<int(final_edits[-1][2])):
                    final_edits.append(edits[i])
                continue
            ###################################

            # Convert edit spans into token ids.
            o_ids = list(range(edits[i][1], edits[i][2])) if edits[i][1] != edits[i][2] else [edits[i][1]] # M on the right
            t_ids = list(range(edits[i][4], edits[i][5]))
            flag = 0
            # Loop through the new MWE edits to see which should replace the old edits
            num_mwe_intersection = 0
            for mwe_e in new_edits:
                # Convert mwe edit spans on the original side into token ids.
                mwe_e_ids = list(range(int(mwe_e[1]), int(mwe_e[2]))) if mwe_e[1] != mwe_e[2] else [int(mwe_e[1])] # M on the right
                # Convert mwe edit spans on the target side into token ids.
                mwe_e_tar_ids = list(range(int(mwe_e[4]), int(mwe_e[5]))) 
    
                # If the MWE wasn't a missing error 
                # If there is intersection between the MWE edit and the original, and 
                # the MWE is not stupidly long, with some arbitrary words in b/ that cause error (based on target) 
                # or if the mwe edit is related to the first or last token of the original span 
                if not mwe_e[0].startswith("M:MWE") and set(mwe_e_ids).intersection(set(o_ids)) and \
                        (int(mwe_e[5])-int(mwe_e[4])<8 or int(mwe_e[1])==int(edits[i][1]) \
                        or int(mwe_e[2])==int(edits[i][2])):
                    num_mwe_intersection +=1

                    # if the MWE has inersection with UNK
                    if edits[i][0] == "UNK":
                        print("Warning:  MWE intersection with UNK:", mwe_e, edits[i])

                    # if there is some part of the edit before the MWE starts:
                    if o_ids[0]< mwe_e_ids[0] or (edits[i][0][0]=='M' and o_ids[0]==mwe_e_ids[0]): 
                        # split the part before the MWE into a new edit
                        split_edit = [edits[i][0], str(o_ids[0]), str(mwe_e_ids[0]), 
                                " ".join(edits[i][3].split(' ')[0:mwe_e_ids[0]-o_ids[0]]), edits[i][4], mwe_e[4],
                                " ".join(edits[i][6].split(" ")[0:int(mwe_e[4])-int(edits[i][4])])]
                        
                        if not (split_edit[6]=='' and split_edit[0][0]=='M'):
                            # if the edit is now corrected to nothing it should be replaced with U (unnecessay) 
                            if split_edit[6]=='' and split_edit[0][0]=='R':
                                # Edit type changed to "U:"
                                split_edit[0] = "U:"+split_edit[0].split('R:')[1]
                            final_edits.append(split_edit)
    
                        final_edits.append(mwe_e)

                    # if the corrected edit is still longer than mwe
                    #elif len(edits[i][6].split(' '))> len(mwe_e[6].split(' ')):
                    #    corrected_mwe_edit = [mwe_e[0], mwe_e[1],mwe_e[2],mwe_e[3],edits[i][4],edits[i][5],edits[i][6]]
                        #print('corrected_mwe_edit', corrected_mwe_edit)
                    #    final_edits.append(corrected_mwe_edit)

                    # If there is some correction after the mwe
                    elif int(edits[i][5])> int(mwe_e[5]):
                        # First add the MWE edit
                        if mwe_e not in final_edits:
                            final_edits.append(mwe_e)
                        # Then add the rest as a M error
                        m_error = ['M:OTHER', int(mwe_e[2]), int(mwe_e[2]), "", int(mwe_e[5]),
                                int(edits[i][5]), " ".join(edits[i][6].split(' ')[int(mwe_e[5])-int(edits[i][4]):])]
                        final_edits.append(m_error)
                        
                    # The MWE edit is added
                    elif mwe_e not in final_edits:
                        # if the MWE edit is bigger than an error that is already added. This is most
                        # likely the case when we override SPELL error
                        if len(final_edits) and (int(mwe_e[1])==int(final_edits[-1][1]) or int(mwe_e[1])<int(final_edits[-1][1])):
                            final_edits[-1] = mwe_e
                        else:
                            final_edits.append(mwe_e)
                        # If original PUNCT edit is ignored in favour of MWE
                        #if "PUNCT" in edits[i][0]:
                        #    print("MWE edit (a case of PUNCT):", mwe_e, "Final_edits", final_edits)
                
                    flag = 1
                    if num_mwe_intersection>1:  # This never happend for the dev data!
                        print("Warning: Second intersection of MWEs happend for an edit")
                    
                    #break   

                # If there is intersection between the MWE edit and the target side of the original
                # and it wasn't detected by the previous condition.
                # This might be the case when the MWE was originally spread in two edits and the second
                # is not aligned well!
                
                elif set(mwe_e_tar_ids).intersection(set(t_ids)) and \
                        (int(mwe_e[5])-int(mwe_e[4])<8 or int(mwe_e[4])==int(edits[i][4]) \
                        or int(mwe_e[5])==int(edits[i][5])):
                    # if there is some part of the edit before the MWE starts 
                    if t_ids[0]< mwe_e_tar_ids[0]:
                        # if the origin of the edit is also before the mwe
                        if o_ids[0]< mwe_e_ids[0]:
                            # split the part before the MWE into a new edit
                            split_edit = [edits[i][0], str(o_ids[0]), str(mwe_e_ids[0]), 
                                    " ".join(edits[i][3].split(' ')[0:mwe_e_ids[0]-o_ids[0]]), 
                                    edits[i][4], mwe_e[4], 
                                    " ".join(edits[i][6].split(" ")[0:int(mwe_e[4])-int(edits[i][4])])]
                            
                            if not (split_edit[6]=='' and split_edit[0][0]=='M'):
                                final_edits.append(split_edit)
                        
                            final_edits.append(mwe_e)
                    # if the corrected edit is still longer than mwe
                    if int(edits[i][5])> int(mwe_e[5]):
                        # First add the MWE edit
                        if mwe_e not in final_edits:
                            final_edits.append(mwe_e)
                        # Then add the rest  
                        # as a M error if the ending of the mwe edit is the same as the original edit
                        if int(mwe_e[2])==edits[i][2]:
                            m_error = ['M:OTHER', int(mwe_e[2]), int(mwe_e[2]), "", int(mwe_e[5]), 
                                int(edits[i][5]), " ".join(edits[i][6].split(' ')[int(mwe_e[5])-int(edits[i][4]):])] 
                        # as R error if the ending of the MWE is less than the ending of the original edit 
                        elif int(mwe_e[2])<edits[i][2]:
                            m_error = ['R:OTHER', int(mwe_e[2]), int(edits[i][2]), edits[i][3], int(mwe_e[5]),
                                int(edits[i][5]), " ".join(edits[i][6].split(' ')[int(mwe_e[5])-int(edits[i][4]):])]

                        final_edits.append(m_error)
                    
                    elif mwe_e not in final_edits:
                        final_edits.append(mwe_e)
                    flag=1

                
            # No intersection, the original edit is added
            if not flag:
                # If the last MWE edit which is added include this error
                # which means the previous final edit should have changed to a longer sequence
                if len(final_edits) and \
                        final_edits[-1][0]!='UNK' and final_edits[-1][0].split(":")[1].startswith("MWE") and \
                        int(edits[i][1])<int(final_edits[-1][2]):
                            # If the added MWE include part of this edit
                            if int(edits[i][2])>int(final_edits[-1][2]):
                                new_edit = edits[i]
                            else:
                                continue
                            
                # In case of an M edit, it should have the same ending index as the previous final edits
                # Not all M errors after MWE are part of the MWE edit based on index, so we check the text of the edit
                # too in the last bit of the condition
                if len(final_edits) and \
                        final_edits[-1][0]!='UNK' and final_edits[-1][0].split(":")[1].startswith("MWE") and \
                        int(final_edits[-1][5])-int(final_edits[-1][4])>int(final_edits[-1][2])-int(final_edits[-1][1]) and \
                        edits[i][0].split(":")[0]=="M" and edits[i][2] == int(final_edits[-1][2]) and \
                        final_edits[-1][6].endswith(edits[i][6]):
                            print("Warning: intersection wasn't recognised here:")
                            print("mwe_e_ids", mwe_e_ids)
                            print("o_ids", o_ids)
                            print("intersection:", set(mwe_e_ids).intersection(set(o_ids)))
                            print("new_edits:", new_edits)
                            continue
                final_edits.append(edits[i])
                #cur+=1
        # Ignore UNK
        final_e_types = [fe[0].split(":")[1] if fe[0]!='UNK' else "UNK" for fe in final_edits]

        for e in final_edits:
            #out.write(edit_to_m2(e, "0")+"\n")
            m2_edits.append(edit_to_m2(e, "0")+"\n")

        #out.write("\n")    
        m2_edits.append("\n")
        sent_count+=1
        
    print('Out of ', count, 'MWEs in the corrected text, ', corrected, 'are different from the source side')
    print("size of data:", len(new_sentences))
    return new_sentences, new_sentences_cor, m2_edits

def get_sentences_with_tags(mwe_tagged_file, without_tags_file):
    new_sentences = []
    for line1, line2 in zip(mwe_tagged_file, without_tags_file):
        line2 = line2.strip().split()
        c_mwe_ids = extract_mwe_ids(line1)
        new_sent = []
        cur = 0
        if len(c_mwe_ids):
            for mwe in c_mwe_ids:
                    b = mwe[0]
                    e = mwe[1]
                    m_type = mwe[2]
                    #new_sent.extend(line2[cur:b] + ['[MWE]'] + line2[b:e] + ['[/MWE]'])
                    new_sent.extend(line2[cur:b] + ['['+m_type+']'] + line2[b:e] + ['[/'+m_type+']'])
                    cur = e
            new_sent.extend(line2[cur:])
            new_sentences.append(" ".join(new_sent))
        else:
            new_sentences.append(" ".join(line2))
    return new_sentences


# Input 1: An M2 block
# Input 2: The id of the target annotator/reference
# Output 1: The original sentence as a list of tokens
# Output 2: The corrected sentence as a list of tokens
# Output 3: The edits as a list of lists: [cat, o_start, o_end, o_str, c_start, c_end, c_str]
def process_m2(m2, id=0):
    # Split lines in the block
    m2 = m2.split("\n")
    # Orig tokens
    o_sent = m2[0].split()[1:]
    # Cor tokens. Initalised as a copy of orig and updated later
    c_sent = o_sent[:]
    # Edits
    edits = m2[1:]
    # Offset when we apply the edits
    offset = 0
    # Store simplified edits here
    new_edits = []
    # Loop through edits
    for e in edits:
        e = e.split("|||")
        if e[1] =="noop": continue # Ignore noop edits
        coder = int(e[-1])
        if coder != id: continue # Ignore other coders
        span = e[0].split()[1:] # Ignore "A "
        start = int(span[0])
        end = int(span[1])
        cor = e[2].split()
        # Apply the correction
        c_sent[start+offset:end+offset] = cor
        # Create a simplified edit and save it:
        e = [e[1], start, end, " ".join(o_sent[start:end]), start+offset, start+offset+len(cor), " ".join(cor)]
        new_edits.append(e)
        # Update the offset
        offset = offset-(end-start)+len(cor)
    return o_sent, c_sent, new_edits

# Input 1: An edit list: [cat, o_start, o_end, o_str, c_start, c_end, c_str]
# Input 2: The id of the target annotator
# Input 3: A list of strings for the types of MWEs
# Output: The edit formatted as a string in an M2 file. MWE edits in notes
def edit_to_m2(e, id, mwe_type=[]):
    span = " ".join(["A", str(e[1]), str(e[2])])
    m2_e = [span, e[0], e[-1], "REQUIRED", "-NONE-", str(id)]
    if mwe_type: m2_e[4] = "MWE_"+"_".join(mwe_type)
    
    return "|||".join(m2_e)

# An example use for the dev data
if __name__ == "__main__":

    if len(sys.argv)>1:
        config_path = sys.argv[1]
    else:
        print("Missing Argument: please specify the path to the config .json file!")
    with open(config_path) as f:
        config = json.load(f)

    cor_mwe = config["cor-mwe_file"]

    #directory = "Data/dev/MWE-annotated cor/ann1/"

    #file_list = ["bea.dev.A.mwe_ann1.txt", "bea.dev.B.mwe_ann1.txt", "bea.dev.C.mwe_ann1.txt", "bea.dev.N.mwe_ann1.txt"]
    #for filename in file_list: 
    if cor_mwe.endswith(".txt"):
        #cor_mwe = os.path.join(directory, filename)
        cor = config["cor_file"]    # "Data/dev/cor/"+filename.split("mwe_ann1.txt")[0]+"cor"
        orig = config["orig_file"]        # "Data/dev/orig/"+filename.split("mwe_ann1.txt")[0]+"orig"
        m2_file_path = config["m2_file"]           # "Data/dev/m2/"+filename.split("mwe_ann1.txt")[0]+"m2"

        if os.path.isfile(cor) and os.path.isfile(orig):
                
            cor_file_mwe = open(cor_mwe)    # .txt file including MWE tags
            cor_file = open(cor)            # .cor corrected text file
            orig_file = open(orig)          # .orig erroneous text file

            if os.path.isfile(m2_file_path):
                print("m2 file path:", m2_file_path)
                m2_file = open(m2_file_path)
    
                # When we have MWEs for the cor file and we wanna map them back using alignments 
                # to the original file
                # We write the tags both on the orig side and the cor side
                new_sentences, new_sentences_cor, m2_edits = get_sentences_with_mapped_tags_return_m2_edits(cor_file_mwe, 
                                                                    cor_file, orig_file, m2_file)
    
                # OUTPUT
                out_dir = config["output_dir"]
                with open(out_dir + m2_file_path.split("/")[-1].split(".m2")[0]+"-mwe.m2", "w") as f:
                    for e in m2_edits:
                        f.write(e)

            else:
                print("ERROR: m2 file does not exist!", m2_file_path)
        else:   
            print("ERROR: Files", cor, "or", orig, "do not exist!")
