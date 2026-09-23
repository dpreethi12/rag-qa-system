def chunk_text(text, chunk_size, chunk_overlap):
    """
    Split the text into chunks of specified size with specified overlap.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be greater than or equal to 0")    
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be less than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        #print("start:" , start)
        end = start + chunk_size
        # try to avoid cutting mid-sentence:
        # look backward from `end` for a natural breakpoint
        # (paragraph break, then period+space, then any space)
        # and adjust `end` to land there if one exists

        threshold = chunk_size // 2 # 
        if end < len(text):
            # look for paragragh break first
            paragraph_break = text[start:end].rfind("\n\n")
            if paragraph_break != -1 and paragraph_break > threshold:
                end = start + paragraph_break
            else:
                #look for period+space
                sentence_end = text[start:end].rfind(". ")
                if(sentence_end != -1 and sentence_end > threshold):
                    end = start + sentence_end + 1 #+1 to include the period
                else:
                    #look for any space
                    space_end = text[start:end].rfind(" ")
                    if(space_end != -1 and space_end > threshold):
                        end = start + space_end
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((chunk, start, end))

        if end >= len(text):
            break

        start = end - chunk_overlap # move start back by chunk_overlap 

    return chunks  
