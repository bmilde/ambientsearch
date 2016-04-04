import subprocess

goal_goals = []

with ('goal_goals.txt') as goal_goals:
    for line in goal_goals:
        if line[-1] == '\n':
            line = line[:-1]
        goal_goals.append((line.split(' ')[0],int(line.split(' ')[1])))

for myfile,number in goal_goals:
    with codecs.open('TestMaryamTexts.m','r','utf-8') as mat_in:
        mat = mat_in.read()
        mat.replace('<filename_placeholder>',myfile)
        mat.replace('<number_placeholder>',number)

    with codecs.open('TestMaryamTexts2.m','w','utf-8') as mat_out:
        mat_out.write(mat)

     subprocess.call("matlab TestMaryamTexts2.m -r \"try;run('TestMaryamTexts2.m');catch;end;quit\"", shell=True)