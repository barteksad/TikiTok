import { useEffect, useRef } from 'react';

type Props = {
    newLimit: () => void;
    isLoading: boolean;
  }

export default function Loading({
    newLimit,
    isLoading
} : Props) {
    const loadingRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!loadingRef?.current) return;
    
        const observer = new IntersectionObserver(([entry]) => {
          console.debug("Intersecting")
          if (entry.isIntersecting && !isLoading) {
            console.debug(entry.intersectionRatio)
            console.debug("Setting new limit")
            newLimit();
            observer.unobserve(entry.target);
          }
        });
        observer.observe(loadingRef.current);
    }, []);

    return (
        <div ref={loadingRef}>Loading...</div>
    )
}