'use client'

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useMixpanel } from "@/context/MixpanelProvider";

// Constants
export const TOKEN_KEY = 'emmi.auth.token';

// Create the context
const AuthContext = createContext(undefined);

// Create the provider component
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null); // Initialize user state to null
    const [loadingUser, setLoadingUser] = useState(true); // Initialize loading state to true
    const [error, setError] = useState(null); // Initialize error state to null
    const router = useRouter();

    // Call useMixpanel at the component's top-level
    const mixpanel = useMixpanel();

    // Function to get the token from local storage
    const getToken = () => {
        return localStorage.getItem(TOKEN_KEY);
    };

    const fetchUser = async () => {
        setError(null);
        const token = getToken();
        if (token) {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/users/me/`, {
                    headers: {
                        'Authorization': `Token ${token}`,
                    },
                });
                const data = await response.json();
                if (data.detail) {
                    setError('Invalid token');
                    throw new Error('Invalid token');
                }
                setUser({ ...data, token });
                mixpanel.identify(data)
            } catch (error) {
                setUser(null);
                mixpanel.reset();
            } finally {
                setLoadingUser(false);
            }
        } else {
            setLoadingUser(false);
        }
    };

    useEffect(() => {
        fetchUser();
    }, []);

    const updateAuthenticatedUser = async () => {
        // re fetch  and updates the user data
        await fetchUser();
    }

    const loginWithToken = async (token) => {
        console.log('Logging in with token');
        setError(null);
        localStorage.setItem(TOKEN_KEY, token);
    
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/users/me/`, {
                headers: {
                    'Authorization': `Token ${token}`,
                },
            });
            const data = await response.json();
    
            if (data.detail) {
                setError('Invalid token');
                throw new Error('Invalid token');
            }
    
            setUser({ ...data, token });
            mixpanel.identify(data)
        } catch (error) {
            setUser(null);
            mixpanel.reset();
        }
    };

    const logout = () => {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
        mixpanel.reset();
        console.log('User logged out');
        router.push('/');
    };

    return (
        <AuthContext.Provider value={{ user, loadingUser, loginWithToken, logout, getToken, error, updateAuthenticatedUser }}>
            {children}
        </AuthContext.Provider>
    );
};

// Custom hook to use the AuthContext
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};