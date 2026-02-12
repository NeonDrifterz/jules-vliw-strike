#!/usr/bin/env python3
"""
Swarm Commander CLI
The unified interface for Jules agents to interact with the Hive Mind and the Fleet.
"""
import sys
import argparse
import os
from penfield_link import PenfieldClient
from jules_core import JulesCore

class SwarmCommander:
    def __init__(self):
        try:
            self.penfield = PenfieldClient()
            self.jules = JulesCore()
        except Exception as e:
            print(f"[Commander] Warning: Initialization incomplete: {e}")

    def log(self, message, m_type="fact", tags=None):
        print(f"[Commander] Logging to Hive Mind: {message[:50]}...")
        return self.penfield.store_memory(message, memory_type=m_type, tags=tags)

    def search(self, query):
        print(f"[Commander] Searching Hive Mind for: {query}")
        return self.penfield.search_memories(query)

    def spawn(self, mission):
        print(f"[Commander] Spawning recursive worker...")
        return self.jules.spawn(mission)

def main():
    parser = argparse.ArgumentParser(description="Swarm Commander CLI")
    subparsers = parser.add_subparsers(dest="command")

    # log
    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("message")
    log_parser.add_argument("--type", default="fact")
    log_parser.add_argument("--tags", help="Comma-separated tags")

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_parser("query")

    # spawn
    spawn_parser = subparsers.add_parser("spawn")
    spawn_parser.add_argument("mission")

    args = parser.parse_args()
    commander = SwarmCommander()

    if args.command == "log":
        tags = args.tags.split(",") if args.tags else []
        commander.log(args.message, m_type=args.type, tags=tags)
    elif args.command == "search":
        res = commander.search(args.query)
        print(res)
    elif args.command == "spawn":
        commander.spawn(args.mission)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
