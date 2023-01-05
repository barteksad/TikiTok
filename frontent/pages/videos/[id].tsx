import { useState, useEffect } from "react";
import Image from 'next/image'
import styles from "../../styles/Video.module.css";

type Props = {
  id: string;
}

const Video = ({ id }: Props) => {
  const [like, setLike] = useState(false);
  const [likesCount, setLikesCount] = useState(0);
  const handleLikeClikc = async () => {
    setLike(!like);
  }

  const url = `https://iframe.mediadelivery.net/embed/83596/${id}?autoplay=true&loop=true`;

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