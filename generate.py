import random as rnd
import shutil
import json
import sys
import re

from generator import *


seed = rnd.randint(0, 9999999999)
random = rnd.Random()

target = 30
output = "gen/speedrnd_datapack"
funcpath = "/data/speedrnd/functions"
header = """## @Author Siandfrance
# This file is autogenerated"""


#%% parse arguments
for arg in sys.argv:
    match = re.match("(?:--seed|-s)=(\\d{1,10})", arg)
    if match:
        seed = int(match.group(1))
    match = re.match("(?:--target|-t)=(\\d{1,3})", arg)
    if match:
        target = int(match.group(1))
    match = re.match("(?:--output|-o)=((?:\\w|/|\\s|\\.)+)", arg)
    if match:
        output = match.group(1)

random.seed(seed)
print(output)


#%% get advancements
advancements: list
with open("advancement_list.json") as f:
    advancements = json.load(f)


print("====================")
print(f"seed = {seed}")
print(f"target = {target}")
print("====================\n")


selection = []
score = 0
while score < target:
    adv = random.choice(advancements)
    advancements.remove(adv)
    if score + adv["score"] <= target:
        selection.append(adv)
        score += adv["score"]

selection.sort(key = lambda adv: adv["score"])


#%% copy files
try:
    shutil.copytree("template/", output)
except FileExistsError:
    pass


#%% setup generators

gens = [
    {
        "path": output + funcpath + "/gen/load.mcfunction",
        "gen": Generator([
            header,
            r'tellraw @a [{"text":"==============================","bold":true},{"text":"\n"},{"text":"--- Speedrnd datapack loaded ---","color":"green"},{"text":"\nMade by "},{"text":"Siandfrance","color":"#820CCE"},{"text":"\n\nSeed: %var%seed%%\n"},{"text":"==============================","bold":true}]'.replace("%var%seed%%", str(seed))
        ])
    },
    {
        "path": output + funcpath + "/gen/display.mcfunction",
        "gen": Generator([
            header,
            r'tellraw @s [{"text":"==============================","bold":true},{"text":"\n"},{"text":"----------- Speedrnd ----------","color":"green"}]',
            TemplateItem(
                r'''scoreboard players set @s srnd 0
execute if entity @s[advancements={%adv_loc%adv%%=true}] run scoreboard players set @s srnd 1
execute if score @s srnd matches 0 run tellraw @s [{"text": "%adv_name%adv%%", "color": "%adv_color%adv%%"}, {"text": ": ", "color": "white"}, {"text": "in progress", "color": "red"}]
execute if score @s srnd matches 1 run tellraw @s [{"text": "%adv_name%adv%%", "color": "%adv_color%adv%%"}, {"text": ": ", "color": "white"}, {"text": "completed", "color": "green"}]
''',
                [Variable("adv", range(len(selection)))],
                {
                    "adv_name": lambda i: selection[i]["name"].replace("\"", "\\\""),
                    "adv_loc" : lambda i: selection[i]["location"],
                    "adv_color": lambda i: "dark_gray" if selection[i]["score"] < 20 else "#790BB1"
                }
            ),
            r'tellraw @s [{"text":"==============================","bold":true}]'
        ])
    },
    {
        "path": output + funcpath + "/gen/check_adv.mcfunction",
        "gen": Generator([
            header,
            r'scoreboard players set \$ok srnd 1',
            TemplateItem(
                r'''execute as @a if entity @s[advancements={%adv_loc%adv%%=true}] run advancement grant @a[advancements={%adv_loc%adv%%=false}] only %adv_loc%adv%%
execute as @a if entity @s[advancements={%adv_loc%adv%%=false}] run scoreboard players set \$ok srnd 0
''',
                [Variable("adv", range(len(selection)))],
                {
                    "adv_name": lambda i: selection[i]["name"].replace("\"", "\\\""),
                    "adv_loc" : lambda i: selection[i]["location"],
                    "adv_color": lambda i: "dark_gray" if selection[i]["score"] < 20 else "#790BB1"
                }
            )
        ])
    }
]


#%% generate files

for gen in gens:
    with open(gen["path"], "w") as f:
        f.write(str(gen["gen"]))
