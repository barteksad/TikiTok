import React from 'react'
import useSWR from 'swr'
import { useAuth } from '../context/AuthContext';
import Video from './videos/[id]';

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
    <div>

      <div>
        {data ?
          data.ids.map((id) => <Video key={id} id={id}></Video>)
          : 'loading..'}
      </div>
    </div>
  )
}

export default Dashboard