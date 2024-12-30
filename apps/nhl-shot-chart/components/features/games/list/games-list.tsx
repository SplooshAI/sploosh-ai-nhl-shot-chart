'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { format } from 'date-fns'
import { GameCard } from '../card/game-card'
import { RefreshSettings } from '@/components/shared/refresh/refresh-settings'
import type { NHLEdgeScheduleResponse } from '@/types/nhl-edge'
import { getScores } from '@/lib/api/nhl-edge'

interface GamesListProps {
    date: Date
    onGameSelect?: (gameId: number) => void
    onClose?: () => void
}

export function GamesList({ date, onGameSelect, onClose }: GamesListProps) {
    const [scheduleData, setScheduleData] = useState<NHLEdgeScheduleResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null)
    const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false)
    const containerRef = useRef<HTMLDivElement>(null)

    const fetchGames = useCallback(async () => {
        try {
            const scrollContainer = containerRef.current?.closest('.overflow-y-auto')
            const scrollPosition = scrollContainer?.scrollTop

            const formattedDate = format(date, 'yyyy-MM-dd')
            const data = await getScores(formattedDate)

            setScheduleData(data)
            setLastRefreshTime(new Date())

            if (scrollPosition !== undefined) {
                requestAnimationFrame(() => {
                    scrollContainer?.scrollTo({
                        top: scrollPosition,
                        behavior: 'instant'
                    })
                })
            }
        } catch (err) {
            console.error('Error fetching games:', err)
            setError('Failed to load games')
        } finally {
            setLoading(false)
        }
    }, [date])

    // Initial fetch on mount
    useEffect(() => {
        fetchGames()
    }, [fetchGames])

    // Auto-refresh effect
    useEffect(() => {
        let timer: NodeJS.Timeout | null = null

        if (autoRefreshEnabled) {
            // Only set up the interval, no immediate fetch
            timer = setInterval(fetchGames, 20000)
        }

        return () => {
            if (timer) {
                clearInterval(timer)
            }
        }
    }, [autoRefreshEnabled, fetchGames])

    if (loading) return (
        <div className="flex justify-center items-center p-4">
            <div className="text-sm text-muted-foreground">Loading games...</div>
        </div>
    )

    if (error) return (
        <div className="p-4">
            <div className="text-sm text-destructive">{error}</div>
        </div>
    )

    if (!scheduleData?.games || scheduleData.games.length === 0) return (
        <div className="p-4">
            <div className="text-sm text-muted-foreground">No games scheduled</div>
        </div>
    )

    return (
        <div className="space-y-4" ref={containerRef}>
            <RefreshSettings
                isEnabled={autoRefreshEnabled}
                onToggle={setAutoRefreshEnabled}
                lastRefreshTime={lastRefreshTime}
            />

            <div className="space-y-2">
                {scheduleData.games.map((game) => (
                    <GameCard
                        key={game.id}
                        game={game}
                        onSelectGame={onGameSelect}
                        onClose={onClose}
                    />
                ))}
            </div>

            <div className="pt-4 mt-4 border-t border-border/50">
                <RefreshSettings
                    isEnabled={autoRefreshEnabled}
                    onToggle={setAutoRefreshEnabled}
                    lastRefreshTime={lastRefreshTime}
                />
            </div>
        </div>
    )
} 