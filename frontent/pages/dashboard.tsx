import React from 'react'
import useSWR from 'swr'
import { useAuth } from '../context/AuthContext';
import Video from './videos/[id]';
import styles from "../styles/Dashboard.module.css";

const content_fetcher = (token: String) => {
  return fetch("http://localhost:3001/content", { method: "GET", headers: { "Authorization": `Bearer ${token}` } }).then((res) => res.json());
}

const Dashboard = () => {
  const { user } = useAuth();
  const { data, error } = useSWR<{
    ids: Array<string>
  }>(
    user.idToken,
    content_fetcher
  );

  if (error) console.debug(error);
  if (data) console.debug(data);

  return (
      <div className={styles.container}>
        {data ?
          data.ids.map((id) => <div key={id} className={styles.child}>
            <Video id={id} ></Video>
          </div>)
          : 'loading..'}
      </div>
  )
}

export default Dashboard