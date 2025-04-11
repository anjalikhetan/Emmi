'use client'

import React, { useState, useCallback, useContext, createContext } from 'react'
import NotFoundContent from '@/components/NotFoundContent'


// Create context
const NotFoundContext = createContext(null)

// Hook to consume context
export const useNotFound = () => {
    const context = useContext(NotFoundContext)
    if (!context) {
        throw new Error("useNotFound must be used within a With404Boundary")
    }
    return context // This should be an object like { markNotFound }
}

// Boundary component
export default function With404Boundary({ children }) {
    const [notFound, setNotFound] = useState(false)

    const markNotFound = useCallback(() => {
        setNotFound(true)
    }, [])

    if (notFound) return <NotFoundContent />

    return (
        <NotFoundContext.Provider value={{ markNotFound }}>
            {children}
        </NotFoundContext.Provider>
    )
}