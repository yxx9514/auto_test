

def str_count(s):
    if s:
        count = {}
        for i in s:
            if i in count:
                count[i] +=1
            else:
                count[i] = 1
        return count
    return s



def no_duplicates(s):
    if s:
        count = {}
        for i in s:
            if i in count:
                count[i] +=1
            else:
                count[i] = 1
        no_duplicates_list = []
        for i in count:
            if count[i] == 1:
                no_duplicates_list.append(i)
        print(no_duplicates_list)
        if no_duplicates_list ==[]:
            return None
        else:
            return no_duplicates_list[0]





def is_palindrome(s):

    left = 0
    right = len(s) - 1

    while left < right:

        if s[left] != s[right]:
            return False

        left += 1
        right -= 1

    return True

s = "abcba"
print(is_palindrome(s))