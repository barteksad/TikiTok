import styles from "../../styles/Video.module.css";

type Props = {
    id: string;
}

const Video = ({ id }: Props) => {
    const url = `https://iframe.mediadelivery.net/embed/83596/${id}?autoplay=true&loop=true`;

    return (
        <div className={styles.div}>
          <iframe
            className={styles.iframe}
            src={url}
            loading="lazy"
            allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture;"
            allowFullScreen={true}>
          </iframe>
        </div>
    )
}

export default Video;