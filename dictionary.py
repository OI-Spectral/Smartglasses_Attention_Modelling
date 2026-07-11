# Source - https://stackoverflow.com/a/69205944
# Posted by fiveobjects, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-17, License - CC BY-SA 4.0

my_dict = {"a": 1, "b": 2, "c": 3}
for key in my_dict:
    print(key + " " + str(my_dict[key]))

# Source - https://stackoverflow.com/a/35864188
# Posted by MSeifert, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-17, License - CC BY-SA 3.0

dataList = [{'a': 1}, {'b': 3}, {'c': 5}]
for index in range(len(dataList)):
    for key in dataList[index]:
        print(dataList[index][key])

