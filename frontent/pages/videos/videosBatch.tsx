import React, { useState } from 'react'
import useSWR from 'swr'
import { useAuth } from '../../context/AuthContext';
import Video from './[id]';
import styles from "../../styles/Dashboard.module.css";
import Loading from '../../components/Loading';

type Props = {
    batch_id: number,
    is_last: boolean,
    new_limit: () => void,
}

const content_fetcher = async ([token, batch_id]: [string, number]) => {
    return fetch(`http://localhost:3001/content/${batch_id}`, { method: "GET", headers: { "Authorization": `Bearer ${token}` } }).then((res) => res.json());
}

const VideosBatch = ({ batch_id, is_last, new_limit }: Props) => {
    const { user } = useAuth();
    const { data, error, isLoading } = useSWR<{
        ids: Array<string>
    }>(
        [user.idToken, batch_id],
        content_fetcher
    );

    if (error) console.debug(error);
    if (data) console.debug(data);

    return (
        <div>
        {data && data.ids ?
            data.ids.map((id, idx) => <div key={idx} className={styles.child}>
                <Video id={id} key={idx}></Video>
            </div>)
            : 'loading..'},
        {(is_last && data && data.ids && data.ids.length > 0 && !isLoading) ?
            <div className={styles.child}>
                <Loading newLimit={new_limit} key={batch_id} isLoading={isLoading}></Loading>
            </div> : null}
        </div>
    )
}

export default VideosBatch;