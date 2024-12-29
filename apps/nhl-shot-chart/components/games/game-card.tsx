import { NHLGame } from '@/types/nhl'
import { format, parseISO } from 'date-fns'

interface GameCardProps {
    game: NHLGame
}

export function GameCard({ game }: GameCardProps) {
    const getGameStatus = () => {
        if (game.gameState === 'LIVE') {
            return `Period ${game.period} - ${game.clock?.timeRemaining}`
        }
        if (game.gameState === 'FUT') {
            return format(parseISO(game.startTimeUTC), 'h:mm a')
        }
        return 'Final'
    }

    return (
        <div className="p-3 rounded-lg bg-background hover:bg-accent cursor-pointer">
            <div className="flex justify-between items-center">
                <div className="space-y-1">
                    <div className="text-sm font-medium">{game.awayTeam.abbrev}</div>
                    <div className="text-sm font-medium">{game.homeTeam.abbrev}</div>
                </div>
                <div className="text-lg font-bold">
                    <div>{game.awayTeam.score ?? '-'}</div>
                    <div>{game.homeTeam.score ?? '-'}</div>
                </div>
            </div>
            <div className="text-xs text-muted-foreground mt-2">
                {getGameStatus()}
            </div>
        </div>
    )
} 