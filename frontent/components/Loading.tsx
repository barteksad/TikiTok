import { useEffect, useRef } from 'react';

type Props = {
    newLimit: () => void;
  }

export default function Loading({
    newLimit
} : Props) {
    const loadingRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!loadingRef?.current) return;
    
        const observer = new IntersectionObserver(([entry]) => {
          console.debug("Intersecting")
          if (entry.isIntersecting) {
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