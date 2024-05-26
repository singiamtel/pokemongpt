import asyncio
from poke_env import AccountConfiguration, ShowdownServerConfiguration

from dotenv import load_dotenv
load_dotenv()

from player import MyPlayer

import os

username = os.getenv('USERNAME')
assert username is not None, "Please set the USERNAME environment variable"
password = os.getenv('PASSWORD')
assert password is not None, "Please set the PASSWORD environment variable"

player = MyPlayer(server_configuration=ShowdownServerConfiguration, account_configuration=AccountConfiguration(username, password), start_timer_on_battle_start=True)


async def main():

    while True:
        print("Waiting for a battle...")
        await player.accept_challenges('itszxc', 1, packed_team=None)
        print("Battle started!")
    # print("Starting the player")
    # await player.ladder(5)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
