from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.player import Player
from colorama import Fore

from dotenv import load_dotenv
load_dotenv()

import os
import json
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def printRed(skk): print(Fore.RED + skk + Fore.RESET)

def prompt_chat(prompt: str):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4o",
        response_format={"type": "json_object"},
    )
    return chat_completion.choices[0].message.content

def findMove(move_id: str, moves: list[Move]):
    for move in moves:
        if move._id == move_id:
            return move
    return None

def findMon(mon_id: str, mons: dict[str, Pokemon]):
    for mon in mons.values():
        if mon.species == mon_id:
            return mon
    return None

class MyPlayer(Player):
    last_choice = None
    def format_team(self, team: dict[str, Pokemon]):
        team_str = ""
        if len(team) < 6:
            team_str += f"There are {6 - (len(team) )} unknown pokemons in the team\n"
        for v in team.values():
            if v.fainted:
                continue
            moves = [move.id for move in v.moves.values()]
            # if any stat is boosted, show it
            boosts = ""
            for stat, boost in v.boosts.items():
                if boost > 0:
                    boosts += f"+{boost} {stat} "
                elif boost < 0:
                    moves.append(f"-{boost} {stat}")
            team_str += f"{v.species}@{v.item} status:{v.status} hp:{v.current_hp_fraction*100:.2f}% {v.ability} {moves} {boosts}\n"
        return team_str 

    def format_prompt(self, battle):
        response = f'''You are in a Pokemon battle. Your team is:
{self.format_team(battle.team)}


Your opponent's team is:
{self.format_team(battle.opponent_team)}


(You {battle.can_tera and "can" or "can't"} use tera)

Your current pokemon is {battle.active_pokemon.species} with {battle.active_pokemon.current_hp_fraction*100:.2f}% hp left. The opponent's current pokemon is {battle.opponent_active_pokemon.species} with {battle.opponent_active_pokemon.current_hp_fraction*100:.2f}% hp left.

Remember that you can't switch to the current pokemon, or a fainted one.

You can ONLY use the following moves, or switch to another pokemon:
{battle.available_moves}

Last turn, you used {self.last_choice or "nothing"}. Be careful of always switching and not making any progress.

What is your choice? There might be several good choices, but always pick the best one.

Return a json object with the key "action" and the value being either the move id or the pokemon name, and another key called "why" to explain your reasoning. For example:
{{"action": "tackle", "why": "It's the only move I have left"}}
{{"action": "pikachu", "why": "Pikachu has a type advantage"}}
        '''
        return response

    def choose_move(self, battle):
        try:
            prompt = self.format_prompt(battle)
            response = prompt_chat(prompt)
            if not response:
                printRed("No response, choosing random move")
                return self.choose_random_move(battle)
            key = json.loads(response)["action"]
            why = json.loads(response)["why"]
            if key in list(map(lambda x: x._id, battle.available_moves)):
                print(f"Choosing move {key} because {why}")
                move = findMove(key, battle.available_moves)
                if not move:
                    raise Exception("Move not found", key, battle.available_moves)
                return self.create_order(move)
            elif key in list(map(lambda x: x.species, battle.team.values())):
                print(f"Switching to {key} because {why}")
                mon = findMon(key, battle.team)
                if not mon:
                    raise Exception("Mon not found", key, battle.team)
                elif mon.active:
                    raise Exception("Mon already active", mon)
                return self.create_order(mon)
            else:
                printRed("No valid move found, choosing random move")
                return self.choose_random_move(battle)

        except Exception as e:
            printRed(f"Error: {e}")
            printRed("Choosing random move")
            return self.choose_random_move(battle)

