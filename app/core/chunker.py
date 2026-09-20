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
        print("start:" , start)
        end = start + chunk_size
        # try to avoid cutting mid-sentence:
        # look backward from `end` for a natural breakpoint
        # (paragraph break, then period+space, then any space)
        # and adjust `end` to land there if one exists
        # need to only accept a found boundary if it's far enough into the window — say, past 50% of chunk_size — otherwise ignore it and fall through to the next-best option (or the raw chunk_size cutoff). Add that threshold check into each of your three boundary searches.
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


#call the chunk_text function with the text, chunk_size, and chunk_overlap parameters
text = ("""805 is before your original start of 1000. You've moved backward. Next iteration, the same thing can happen again, and start keeps sliding backward instead of progressing through the document — in the worst case this either loops for a very long time re-processing the same region, or start eventually goes negative, at which point text[start:end] starts doing Python's negative-indexing (counting from the end of the string), giving you garbage chunks.

Try to reproduce this yourself: build a test string where a \n\n lands very close to the start of a chunk window, run your function, and watch what start does across iterations — print it each loop.

The fix: you found a real natural boundary, but it's too close to start to be useful — using it would make the chunk absurdly small and break the forward-progress guarantee. You need to only accept a found boundary if it's far enough into the window — say, past 50% of chunk_size — otherwise ignore it and fall through to the next-best option (or the raw chunk_size cutoff). Add that threshold check into each of your three boundary searches.""")
chunk_overlap = 20
chunk_size = 100

chunks = chunk_text(text, chunk_size, chunk_overlap)
print(chunks[10], chunks[11])
