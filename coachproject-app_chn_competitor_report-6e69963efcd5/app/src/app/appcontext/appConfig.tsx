"use client"
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Environment = 'dev' | 'qa' | 'prd';

interface AppConfigType {
  destinationUrl: string,
  envVal: string,
  windowLocation: string
}

interface AppConfigProviderProps {
  children: ReactNode
}

const AppConfigContext = createContext<AppConfigType | undefined>(undefined);


export const AppConfigProvider: React.FC<AppConfigProviderProps> = ({ children }) => {
  const [destinationUrl, setDestinationUrl] = useState('');
  const [envVal, setEnvVal] = useState('dev');
  const [windowLocation, setWindowLocation] = useState('')


  useEffect(() => {
    setWindowLocation(window.location.origin);
  }, [])
  useEffect(() => {

    if (windowLocation === 'http://localhost:3000') {
      setDestinationUrl("http://localhost:8000/backend")
      setEnvVal('dev');
    }

    if (windowLocation === 'https://competitorapp.analytics.tapestry.com') {
      setDestinationUrl("https://competitorapp.analytics.tapestry.com/backend")
      setEnvVal('dev');
    }

    if ((windowLocation === 'https://competitorapp-mlc-qa.global.coach.com')) {
      setDestinationUrl("http://localhost/backend")
      setEnvVal('qa');
    }

    if ((windowLocation === 'https://competitorapp-mlc.global.coach.com')) {
      setDestinationUrl("http://localhost/backend")
      setEnvVal('prd');
    }

  }, [windowLocation])


  return (
    <AppConfigContext.Provider value={{
      destinationUrl,
      envVal,
      windowLocation
    }}>
      {children}
    </AppConfigContext.Provider>
  );
};

export const useAppConfigContext = (): AppConfigType => {
  const context = useContext(AppConfigContext);
  if (!context) {
    throw new Error('useAppConfigContext must be used within an AppConfigProvider');
  }
  return context;
};
