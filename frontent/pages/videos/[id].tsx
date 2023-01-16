import { useState, useEffect } from "react";
import Image from 'next/image'
import styles from "../../styles/Video.module.css";
import { useAuth } from "../../context/AuthContext";

type Props = {
  id: string;
}

type LikeResponse = {
  liked: boolean;
  likes_count: number;
}

const like_clicker = async (token: String, video_id: String) => {
  return fetch(`http://localhost:8002/like_clicked/${video_id}`, { 
    method: "POST", 
    headers: { 
      "Authorization": `Bearer ${token}` 
    } 
  }).then((res) => res.json()); 
}

const like_fetcher = async (token: String, video_id: String) => {
  return fetch(`http://localhost:8002/get_likes/${video_id}`, { 
    method: "GET", 
    headers: { 
      "Authorization": `Bearer ${token}` 
    } 
  }).then((res) => res.json()); 
}

const Video = ({ id }: Props) => {
  const { user } = useAuth();
  const [like, setLike] = useState(false);
  const [likesCount, setLikesCount] = useState(0);

  useEffect(() => {
    const fetch_likes = async () => {
      const resp: LikeResponse = await like_fetcher(user.idToken, id);
      console.debug("fetch like response");
      console.debug(resp);
      setLike(resp.liked);
      setLikesCount(resp.likes_count);
    }
    fetch_likes();
  }, [like])

  const handleLikeClikc = async () => {
    const resp = await like_clicker(user.idToken, id);
    console.debug(resp);
    setLike(!like);
  }

  const url = `https://iframe.mediadelivery.net/embed/88735/${id}?autoplay=true&loop=true`;

  return (
    <div className={styles.videoDiv}>
      <iframe
        className={styles.videoIframe}
        src={url}
        loading="lazy"
        allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture;"
        allowFullScreen={true}>
      </iframe>
      <div className={styles.likeButton} onClick={handleLikeClikc}>
        <Image 
        src={like ? "/heart-filled.svg" : "/heart-notfilled.svg" }
        alt={""} 
        width={100} 
        height={100}></Image>
        <p className={styles.likesCount}>{likesCount}</p>
      </div>
    </div>
  )
}

export default Video;