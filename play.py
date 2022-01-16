from scopone_scientifico import Tournament

def main() -> None:
    tournament = Tournament(
        team1=(..., 'B'), 
        team2=('C', 'D'),
        n_match=1
    )
    tournament.run()

if __name__ == '__main__':
    main()