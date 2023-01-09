import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext';
import styles from "../styles/Dashboard.module.css";
import VideosBatch from './videos/videosBatch';

const Dashboard = () => {
  const [nPart, setNPart] = useState(0);

  const videos_batches = []
  for(let i=0; i < nPart + 1; i++) {
    videos_batches.push(<VideosBatch batch_id={i} is_last={i === nPart} new_limit= {() => setNPart(nPart + 1)} key={i}/>);
  }

  return (
    <div className={styles.container}>
      {videos_batches}
    </div>
  )
}

export default Dashboard